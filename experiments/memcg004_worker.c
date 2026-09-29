#define _GNU_SOURCE
#include <fcntl.h>
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <unistd.h>

static void touch_page(unsigned char *region, long page_size, int page_index) {
    region[(size_t)page_index * (size_t)page_size] =
        (unsigned char)((page_index + 1) & 0xff);
}

int main(int argc, char **argv) {
    const char *control_path = NULL;
    const char *status_path = NULL;
    int max_pages = 256;
    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--control") == 0 && i + 1 < argc) control_path = argv[++i];
        else if (strcmp(argv[i], "--status") == 0 && i + 1 < argc) status_path = argv[++i];
        else if (strcmp(argv[i], "--max-pages") == 0 && i + 1 < argc) max_pages = atoi(argv[++i]);
        else return 2;
    }
    if (!control_path || !status_path || max_pages < 128) return 2;
    long page_size = sysconf(_SC_PAGESIZE);
    if (page_size <= 0) return 2;
    size_t region_size = (size_t)max_pages * (size_t)page_size;
    unsigned char *region = mmap(NULL, region_size, PROT_READ | PROT_WRITE,
        MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (region == MAP_FAILED) return 2;

    FILE *status = fopen(status_path, "a");
    if (!status) return 2;
    setvbuf(status, NULL, _IOLBF, 0);

    /* Deliberately zero measured-page touches before READY. */
    int touched = 0;
    struct rusage ru;
    if (getrusage(RUSAGE_SELF, &ru) != 0) return 2;
    fprintf(status, "READY cpu=%d page_size=%ld touched=0 minor_faults=%ld\n",
            sched_getcpu(), page_size, ru.ru_minflt);

    int fd = open(control_path, O_RDWR | O_CLOEXEC);
    if (fd < 0) return 2;
    FILE *control = fdopen(fd, "r");
    if (!control) return 2;

    char line[128];
    while (fgets(line, sizeof(line), control)) {
        if (strncmp(line, "TOUCH_ONE", 9) == 0) {
            if (touched >= max_pages) {
                fprintf(status, "ERROR max_pages\n");
                continue;
            }
            touch_page(region, page_size, touched++);
            if (getrusage(RUSAGE_SELF, &ru) != 0) return 2;
            fprintf(status, "TOUCH count=%d cpu=%d minor_faults=%ld\n",
                    touched, sched_getcpu(), ru.ru_minflt);
        } else if (strncmp(line, "STOP", 4) == 0) {
            fprintf(status, "STOP cpu=%d touched=%d\n", sched_getcpu(), touched);
            break;
        } else {
            fprintf(status, "ERROR command\n");
        }
    }
    fclose(control);
    fclose(status);
    munmap(region, region_size);
    return 0;
}
