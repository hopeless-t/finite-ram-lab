#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/prctl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#define CONTROL_BYTES 4096

#define OFF_READY 0
#define OFF_COMMAND 4
#define OFF_DONE 8
#define OFF_STOP 12
#define OFF_TARGET_CPU 16
#define OFF_OBSERVED_CPU 20
#define OFF_TOUCHED 24
#define OFF_ERROR 28
#define OFF_UNMAPPED 32
#define OFF_PAGE_SIZE 36
#define OFF_REGION_ADDR 40
#define OFF_MAX_PAGES 48

#define CMD_TOUCH 1
#define CMD_UNMAP 2

#define ERR_NONE 0
#define ERR_CPU 1
#define ERR_RANGE 2
#define ERR_UNMAPPED 3
#define ERR_COMMAND 4
#define ERR_MUNMAP 5

static uint32_t load_u32(void *base, size_t off) {
    return __atomic_load_n((uint32_t *)((char *)base + off), __ATOMIC_ACQUIRE);
}

static void store_u32(void *base, size_t off, uint32_t value) {
    __atomic_store_n((uint32_t *)((char *)base + off), value, __ATOMIC_RELEASE);
}

static void store_u64(void *base, size_t off, uint64_t value) {
    __atomic_store_n((uint64_t *)((char *)base + off), value, __ATOMIC_RELEASE);
}

static void usage(const char *prog) {
    fprintf(stderr,
            "usage: %s --shared PATH --role producer|trigger|scrubber "
            "--max-pages N\n",
            prog);
}

int main(int argc, char **argv) {
    const char *shared = NULL;
    const char *role = NULL;
    unsigned long max_pages = 64;

    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--shared") && i + 1 < argc) {
            shared = argv[++i];
        } else if (!strcmp(argv[i], "--role") && i + 1 < argc) {
            role = argv[++i];
        } else if (!strcmp(argv[i], "--max-pages") && i + 1 < argc) {
            max_pages = strtoul(argv[++i], NULL, 10);
        } else {
            usage(argv[0]);
            return 2;
        }
    }

    if (!shared || !role || max_pages == 0) {
        usage(argv[0]);
        return 2;
    }

    const char *comm = NULL;
    if (!strcmp(role, "producer"))
        comm = "frlprod";
    else if (!strcmp(role, "trigger"))
        comm = "frltrig";
    else if (!strcmp(role, "scrubber"))
        comm = "frlscrub";
    else {
        usage(argv[0]);
        return 2;
    }

    if (prctl(PR_SET_NAME, comm, 0, 0, 0) != 0) {
        perror("prctl(PR_SET_NAME)");
        return 3;
    }

    int fd = open(shared, O_RDWR);
    if (fd < 0) {
        perror("open shared");
        return 4;
    }

    void *ctl = mmap(NULL, CONTROL_BYTES, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (ctl == MAP_FAILED) {
        perror("mmap shared");
        close(fd);
        return 5;
    }

    long page_size = sysconf(_SC_PAGESIZE);
    if (page_size <= 0) {
        fprintf(stderr, "invalid page size\n");
        return 6;
    }

    size_t region_size = (size_t)max_pages * (size_t)page_size;
    unsigned char *region = mmap(NULL, region_size, PROT_READ | PROT_WRITE,
                                 MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (region == MAP_FAILED) {
        perror("mmap region");
        return 7;
    }

#ifdef MADV_NOHUGEPAGE
    if (madvise(region, region_size, MADV_NOHUGEPAGE) != 0) {
        perror("madvise(MADV_NOHUGEPAGE)");
        return 8;
    }
#endif

    memset(ctl, 0, CONTROL_BYTES);
    store_u32(ctl, OFF_PAGE_SIZE, (uint32_t)page_size);
    store_u32(ctl, OFF_MAX_PAGES, (uint32_t)max_pages);
    store_u64(ctl, OFF_REGION_ADDR, (uint64_t)(uintptr_t)region);
    store_u32(ctl, OFF_READY, 1);

    while (!load_u32(ctl, OFF_STOP)) {
        uint32_t cmd = load_u32(ctl, OFF_COMMAND);
        if (cmd == 0) {
            usleep(50);
            continue;
        }

        store_u32(ctl, OFF_DONE, 0);
        store_u32(ctl, OFF_ERROR, ERR_NONE);

        if (cmd == CMD_TOUCH) {
            if (load_u32(ctl, OFF_UNMAPPED)) {
                store_u32(ctl, OFF_ERROR, ERR_UNMAPPED);
            } else {
                uint32_t index = load_u32(ctl, OFF_TOUCHED);
                if (index >= max_pages) {
                    store_u32(ctl, OFF_ERROR, ERR_RANGE);
                } else {
                    int cpu = sched_getcpu();
                    store_u32(ctl, OFF_OBSERVED_CPU, (uint32_t)cpu);
                    uint32_t target = load_u32(ctl, OFF_TARGET_CPU);
                    if ((uint32_t)cpu != target) {
                        store_u32(ctl, OFF_ERROR, ERR_CPU);
                    } else {
                        volatile unsigned char *p =
                            region + ((size_t)index * (size_t)page_size);
                        *p = (unsigned char)(index + 1);
                        store_u32(ctl, OFF_TOUCHED, index + 1);
                    }
                }
            }
        } else if (cmd == CMD_UNMAP) {
            if (!load_u32(ctl, OFF_UNMAPPED)) {
                if (munmap(region, region_size) != 0) {
                    store_u32(ctl, OFF_ERROR, ERR_MUNMAP);
                } else {
                    region = NULL;
                    store_u32(ctl, OFF_UNMAPPED, 1);
                }
            }
        } else {
            store_u32(ctl, OFF_ERROR, ERR_COMMAND);
        }

        __atomic_thread_fence(__ATOMIC_SEQ_CST);
        store_u32(ctl, OFF_COMMAND, 0);
        store_u32(ctl, OFF_DONE, 1);
    }

    if (region && !load_u32(ctl, OFF_UNMAPPED))
        munmap(region, region_size);
    munmap(ctl, CONTROL_BYTES);
    close(fd);
    return 0;
}
