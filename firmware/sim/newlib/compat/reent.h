/* Stand-in for newlib's <reent.h>: the PC has no newlib reentrancy structure, so its helpers map to plain libc. */
#include <stdlib.h>
struct _reent;
#define _REENT ((struct _reent *)0)
#define _getenv_r(r, name) getenv(name)
#define _malloc_r(r, n) malloc(n)
