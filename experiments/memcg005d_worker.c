#define _GNU_SOURCE
#include <fcntl.h>
#include <sched.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

struct control_page {
    _Atomic uint32_t ready;
    _Atomic uint32_t mode;
    _Atomic uint32_t target_cpu;
    _Atomic uint32_t go;
    _Atomic uint32_t done;
    _Atomic uint32_t stop;
    _Atomic uint32_t observed_cpu;
    _Atomic uint32_t touched;
    _Atomic uint32_t error;
};

static inline void cpu_relax(void) {
#if defined(__x86_64__) || defined(__i386__)
    __asm__ __volatile__("pause" ::: "memory");
#else
    atomic_signal_fence(memory_order_seq_cst);
#endif
}

static void touch_page(unsigned char *region, long page_size, int page_index) {
    region[(size_t)page_index * (size_t)page_size] =
        (unsigned char)((page_index + 1) & 0xff);
}

static int migrate_to(int cpu) {
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(cpu, &set);
    if (sched_setaffinity(0, sizeof(set), &set) != 0)
        return -1;
    for (int i = 0; i < 1000000; ++i) {
        int seen = sched_getcpu();
        if (seen == cpu)
            return seen;
        cpu_relax();
    }
    return -1;
}

int main(int argc, char **argv) {
    const char *shared_path = NULL;
    int max_pages = 8;
    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--shared") && i + 1 < argc)
            shared_path = argv[++i];
        else if (!strcmp(argv[i], "--max-pages") && i + 1 < argc)
            max_pages = atoi(argv[++i]);
        else
            return 2;
    }
    if (!shared_path || max_pages < 2)
        return 2;

    long page_size = sysconf(_SC_PAGESIZE);
    if (page_size <= 0)
        return 2;

    int sfd = open(shared_path, O_RDWR | O_CLOEXEC);
    if (sfd < 0)
        return 2;
    struct control_page *ctl = mmap(
        NULL, (size_t)page_size,
        PROT_READ | PROT_WRITE, MAP_SHARED, sfd, 0
    );
    if (ctl == MAP_FAILED)
        return 2;

    size_t region_size = (size_t)max_pages * (size_t)page_size;
    unsigned char *region = mmap(
        NULL, region_size, PROT_READ | PROT_WRITE,
        MAP_PRIVATE | MAP_ANONYMOUS, -1, 0
    );
    if (region == MAP_FAILED)
        return 2;

    int touched = 0;
    atomic_store_explicit(&ctl->observed_cpu, (uint32_t)sched_getcpu(), memory_order_release);
    atomic_store_explicit(&ctl->touched, 0, memory_order_release);
    atomic_store_explicit(&ctl->error, 0, memory_order_release);
    atomic_store_explicit(&ctl->ready, 1, memory_order_release);

    while (!atomic_load_explicit(&ctl->stop, memory_order_acquire)) {
        if (!atomic_load_explicit(&ctl->go, memory_order_acquire)) {
            cpu_relax();
            continue;
        }

        uint32_t mode = atomic_load_explicit(&ctl->mode, memory_order_acquire);
        int target = (int)atomic_load_explicit(&ctl->target_cpu, memory_order_acquire);
        int seen = sched_getcpu();

        if (mode == 1) {
            seen = migrate_to(target);
            if (seen != target) {
                atomic_store_explicit(&ctl->error, 1, memory_order_release);
                atomic_store_explicit(&ctl->done, 1, memory_order_release);
                atomic_store_explicit(&ctl->go, 0, memory_order_release);
                continue;
            }
        } else if (mode == 2) {
            if (seen != target) {
                atomic_store_explicit(&ctl->error, 2, memory_order_release);
                atomic_store_explicit(&ctl->done, 1, memory_order_release);
                atomic_store_explicit(&ctl->go, 0, memory_order_release);
                continue;
            }
        } else {
            atomic_store_explicit(&ctl->error, 3, memory_order_release);
            atomic_store_explicit(&ctl->done, 1, memory_order_release);
            atomic_store_explicit(&ctl->go, 0, memory_order_release);
            continue;
        }

        /* Critical interval: no syscall/status I/O before this measured touch. */
        touch_page(region, page_size, touched++);
        atomic_store_explicit(&ctl->observed_cpu, (uint32_t)seen, memory_order_release);
        atomic_store_explicit(&ctl->touched, (uint32_t)touched, memory_order_release);
        atomic_store_explicit(&ctl->done, 1, memory_order_release);
        atomic_store_explicit(&ctl->go, 0, memory_order_release);
    }

    munmap(region, region_size);
    munmap(ctl, (size_t)page_size);
    close(sfd);
    return 0;
}
