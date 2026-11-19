# Operating Systems

## Processes and threads
A process is a program in execution, with its own address space, registers, and open files. A thread is a lightweight unit of execution inside a process. Threads of the same process share the code, data, and heap, but each thread has its own stack and registers. Context switching between threads of one process is cheaper than between processes because the address space does not change.

## Process states
A process moves between the new, ready, running, waiting, and terminated states. The scheduler moves a process from ready to running by dispatching it to the CPU. A running process moves to waiting when it requests I/O and returns to ready when the I/O completes.

## CPU scheduling
First-Come First-Served (FCFS) runs processes in arrival order and suffers from the convoy effect, where short processes wait behind one long process. Shortest Job First (SJF) minimises average waiting time but can cause starvation of long processes. Round Robin gives each process a fixed time quantum and preempts it when the quantum expires, which gives good response time. Priority scheduling can starve low-priority processes. Aging gradually increases the priority of waiting processes to prevent starvation.

## Deadlock
Deadlock occurs when processes wait forever for resources held by each other. Four conditions must hold at the same time: mutual exclusion, hold and wait, no preemption, and circular wait. Breaking any one condition prevents deadlock. The Banker's algorithm avoids deadlock by granting a resource request only if the system stays in a safe state.

## Memory management
Paging divides physical memory into fixed-size frames and logical memory into pages of the same size, which removes external fragmentation. A page table maps page numbers to frame numbers. The translation lookaside buffer (TLB) is a small, fast cache of recent page table entries that speeds up address translation. A page fault occurs when a process accesses a page that is not in memory, and the operating system loads it from disk. Thrashing happens when a system spends more time swapping pages than executing instructions.

## Synchronization
A race condition occurs when the result depends on the order in which threads access shared data. A semaphore is an integer variable accessed only through the atomic wait and signal operations. A binary semaphore works as a mutex lock. A critical section is code that accesses shared resources and must not be executed by more than one thread at a time.
