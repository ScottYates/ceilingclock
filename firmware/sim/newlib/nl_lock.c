/* The lock newlib's time code takes around its shared time-zone state (newlib's tzlock.c uses the
   ESP-IDF lock; the simulator runs threads, so a pthread mutex stands in). */
#ifdef __wasi__   /* the browser build has no threads */
void __tz_lock(void) {}
void __tz_unlock(void) {}
#else
#include <pthread.h>
static pthread_mutex_t tz_mutex = PTHREAD_MUTEX_INITIALIZER;
void __tz_lock(void) { pthread_mutex_lock(&tz_mutex); }
void __tz_unlock(void) { pthread_mutex_unlock(&tz_mutex); }
#endif
