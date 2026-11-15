/* Forced into every newlib file (-include). mktime, localtime_r, gmtime_r and tzset keep their names:
   linked into a program, they replace the PC C library's own for every call in that program (glibc's
   versions stay reachable with dlsym(RTLD_NEXT, ...), which the schedule test uses to compare the two).
   Newlib's internal names get an nl_ prefix so they can't collide with anything in glibc. */
#define _tzset_r          nl__tzset_r
#define _tzset_unlocked   nl__tzset_unlocked
#define _tzset_unlocked_r nl__tzset_unlocked_r
#define __tzcalc_limits   nl__tzcalc_limits
#define __gettzinfo       nl__gettzinfo
#define __month_lengths   nl__month_lengths
#define __tz_lock         nl__tz_lock
#define __tz_unlock       nl__tz_unlock
#define _tzname           nl__tzname
#define _daylight         nl__daylight
#define _timezone         nl__timezone
#define siscanf           sscanf
/* newlib's <time.h> declares these; the PC's does not */
extern char *_tzname[2];
extern int _daylight;
extern long _timezone;
