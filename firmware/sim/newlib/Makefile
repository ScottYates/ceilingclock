# Builds newlib's date functions (unchanged sources from Espressif's newlib, branch esp-4.3.0) as a PC
# library, libnltime.a. Linking it in replaces the PC's mktime, localtime_r, gmtime_r and tzset.
# Used by the simulator and the alarm schedule test.
CC ?= cc
OUT ?= ../build/newlib
SRC := mktime.c lcltime_r.c gmtime_r.c tzset_r.c tzset.c tzcalc_limits.c gettzinfo.c tzvars.c month_lengths.c nl_lock.c
CFLAGS := -O1 -g -w -I. -Icompat -include nl_rename.h -pthread

$(OUT)/libnltime.a: $(SRC:%.c=$(OUT)/%.o)
	ar rcs $@ $^
$(OUT)/%.o: %.c local.h nl_rename.h compat/*.h | $(OUT)
	$(CC) $(CFLAGS) -c $< -o $@
$(OUT):
	mkdir -p $(OUT)
