#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <sys/types.h>
#include <unistd.h>

struct sample {
    int step;
    long long memory_current;
    long long anon;
    long long kernel;
    long long pagetables;
    long long minor_faults;
};

static int read_all_at_start(int fd, char *buf, size_t cap) {
    if (lseek(fd, 0, SEEK_SET) < 0) return -1;
    ssize_t n = read(fd, buf, cap - 1);
    if (n < 0) return -1;
    buf[n] = '\0';
    return (int)n;
}

static long long read_single_value(int fd, char *buf, size_t cap) {
    if (read_all_at_start(fd, buf, cap) < 0) return -1;
    errno = 0;
    char *end = NULL;
    long long v = strtoll(buf, &end, 10);
    if (errno != 0 || end == buf) return -1;
    return v;
}

static long long stat_value(const char *buf, const char *key) {
    size_t keylen = strlen(key);
    const char *p = buf;
    while (*p) {
        const char *line = p;
        const char *nl = strchr(line, '\n');
        size_t len = nl ? (size_t)(nl - line) : strlen(line);
        if (len > keylen + 1 &&
            strncmp(line, key, keylen) == 0 &&
            line[keylen] == ' ') {
            return strtoll(line + keylen + 1, NULL, 10);
        }
        if (!nl) break;
        p = nl + 1;
    }
    return -1;
}

static int own_cgroup_path(char *out, size_t cap) {
    FILE *f = fopen("/proc/self/cgroup", "r");
    if (!f) return -1;
    char line[PATH_MAX + 64];
    int ok = -1;
    while (fgets(line, sizeof(line), f)) {
        if (strncmp(line, "0::", 3) == 0) {
            char *p = line + 3;
            char *nl = strchr(p, '\n');
            if (nl) *nl = '\0';
            if (snprintf(out, cap, "/sys/fs/cgroup%s", p) >= (int)cap) {
                ok = -1;
            } else {
                ok = 0;
            }
            break;
        }
    }
    fclose(f);
    return ok;
}

static int collect_sample(
    struct sample *s,
    int step,
    int fd_current,
    int fd_stat,
    char *current_buf,
    size_t current_cap,
    char *stat_buf,
    size_t stat_cap
) {
    long long cur = read_single_value(fd_current, current_buf, current_cap);
    if (cur < 0) return -1;
    if (read_all_at_start(fd_stat, stat_buf, stat_cap) < 0) return -1;

    struct rusage ru;
    if (getrusage(RUSAGE_SELF, &ru) != 0) return -1;

    s->step = step;
    s->memory_current = cur;
    s->anon = stat_value(stat_buf, "anon");
    s->kernel = stat_value(stat_buf, "kernel");
    s->pagetables = stat_value(stat_buf, "pagetables");
    s->minor_faults = (long long)ru.ru_minflt;
    return 0;
}

int main(int argc, char **argv) {
    const char *mode = NULL;
    int steps = 256;

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--mode") == 0 && i + 1 < argc) {
            mode = argv[++i];
        } else if (strcmp(argv[i], "--steps") == 0 && i + 1 < argc) {
            steps = atoi(argv[++i]);
        } else {
            fprintf(stderr, "unknown argument: %s\n", argv[i]);
            return 2;
        }
    }

    if (!mode || (strcmp(mode, "touch") != 0 && strcmp(mode, "control") != 0)) {
        fprintf(stderr, "--mode touch|control required\n");
        return 2;
    }
    if (steps <= 0 || steps > 4096) {
        fprintf(stderr, "invalid steps\n");
        return 2;
    }

    long page_size = sysconf(_SC_PAGESIZE);
    if (page_size <= 0) {
        perror("sysconf");
        return 2;
    }

    size_t region_size = (size_t)steps * (size_t)page_size;
    unsigned char *region = mmap(
        NULL, region_size, PROT_READ | PROT_WRITE,
        MAP_PRIVATE | MAP_ANONYMOUS, -1, 0
    );
    if (region == MAP_FAILED) {
        perror("mmap region");
        return 2;
    }

    size_t sample_bytes = (size_t)(steps + 1) * sizeof(struct sample);
    struct sample *samples = mmap(
        NULL, sample_bytes, PROT_READ | PROT_WRITE,
        MAP_PRIVATE | MAP_ANONYMOUS, -1, 0
    );
    if (samples == MAP_FAILED) {
        perror("mmap samples");
        return 2;
    }
    memset(samples, 0, sample_bytes);

    char cg[PATH_MAX];
    if (own_cgroup_path(cg, sizeof(cg)) != 0) {
        fprintf(stderr, "cannot resolve cgroup path\n");
        return 2;
    }

    char current_path[PATH_MAX];
    char stat_path[PATH_MAX];
    if (snprintf(current_path, sizeof(current_path), "%s/memory.current", cg) >= (int)sizeof(current_path) ||
        snprintf(stat_path, sizeof(stat_path), "%s/memory.stat", cg) >= (int)sizeof(stat_path)) {
        fprintf(stderr, "cgroup path too long\n");
        return 2;
    }

    int fd_current = open(current_path, O_RDONLY | O_CLOEXEC);
    int fd_stat = open(stat_path, O_RDONLY | O_CLOEXEC);
    if (fd_current < 0 || fd_stat < 0) {
        perror("open cgroup files");
        return 2;
    }

    int cpu = sched_getcpu();
    if (cpu < 0) {
        perror("sched_getcpu");
        return 2;
    }
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(cpu, &set);
    if (sched_setaffinity(0, sizeof(set), &set) != 0) {
        perror("sched_setaffinity");
        return 2;
    }

    char current_buf[256];
    char stat_buf[16384];
    memset(current_buf, 0, sizeof(current_buf));
    memset(stat_buf, 0, sizeof(stat_buf));

    /* Warm parser/read paths before baseline. */
    struct sample warm;
    if (collect_sample(
            &warm, -1, fd_current, fd_stat,
            current_buf, sizeof(current_buf),
            stat_buf, sizeof(stat_buf)) != 0) {
        fprintf(stderr, "warm sample failed\n");
        return 2;
    }

    if (collect_sample(
            &samples[0], 0, fd_current, fd_stat,
            current_buf, sizeof(current_buf),
            stat_buf, sizeof(stat_buf)) != 0) {
        fprintf(stderr, "baseline sample failed\n");
        return 2;
    }

    for (int step = 1; step <= steps; ++step) {
        if (strcmp(mode, "touch") == 0) {
            region[(size_t)(step - 1) * (size_t)page_size] =
                (unsigned char)(step & 0xff);
        }

        if (collect_sample(
                &samples[step], step, fd_current, fd_stat,
                current_buf, sizeof(current_buf),
                stat_buf, sizeof(stat_buf)) != 0) {
            fprintf(stderr, "sample failed at step %d\n", step);
            return 2;
        }
    }

    printf("mode,step,pinned_cpu,page_size,memory_current_bytes,anon_bytes,kernel_bytes,pagetables_bytes,minor_faults\n");
    for (int step = 0; step <= steps; ++step) {
        const struct sample *s = &samples[step];
        printf(
            "%s,%d,%d,%ld,%lld,%lld,%lld,%lld,%lld\n",
            mode, s->step, cpu, page_size,
            s->memory_current, s->anon, s->kernel,
            s->pagetables, s->minor_faults
        );
    }

    close(fd_current);
    close(fd_stat);
    munmap(samples, sample_bytes);
    munmap(region, region_size);
    return 0;
}
