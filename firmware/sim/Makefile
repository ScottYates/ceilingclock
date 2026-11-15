# PC simulator for the Ceiling Clock firmware.
# Compiles the real firmware sources (../src) against stand-ins for the ESP32 hardware in shim/.
# Needs ArduinoJson: run `pio pkg install` (or one `pio run`) in ../ first so .pio/libdeps exists.
FW  := ../src
AJ  := ../.pio/libdeps/esp32s3/ArduinoJson/src
CXX ?= g++
CXXFLAGS := -std=gnu++17 -O1 -g -Wall -Wno-unused-variable -Wno-unused-function -pthread \
            -Ishim -I$(FW) -I$(AJ) -DARDUINO=10819 -DARDUINOJSON_ENABLE_PROGMEM=0
OUT := build
# Local time comes from the ESP32's own C library (newlib): libnltime.a's mktime, localtime_r, gmtime_r
# and tzset replace the PC's at link time, so daylight-saving edges behave exactly as on the clock.
NLTIME := $(OUT)/newlib/libnltime.a

# Every firmware source file, compiled unchanged: src/ has no simulator-only code (make check-src).
FW_SRC := main settings net_fetch_esp audio_lib_fix

all: check-src $(OUT)/ceilingclock-sim

check-src:
	@! grep -nE 'NATIVE_SIM|SIM_[A-Z]' $(FW)/*.cpp $(FW)/*.h || (echo 'firmware source must not have simulator-only code'; false)

$(OUT)/%.o: $(FW)/%.cpp $(FW)/*.h shim/*.h | $(OUT)
	$(CXX) $(CXXFLAGS) -c $< -o $@
$(OUT)/sim_hw.o: sim_hw.cpp shim/*.h | $(OUT)
	$(CXX) $(CXXFLAGS) -c $< -o $@
$(OUT)/sim_main.o: sim_main.cpp | $(OUT)
	$(CXX) $(CXXFLAGS) -c $< -o $@
$(OUT)/ceilingclock-sim: $(FW_SRC:%=$(OUT)/%.o) $(OUT)/sim_hw.o $(OUT)/sim_main.o $(NLTIME)
	$(CXX) $(CXXFLAGS) $^ -o $@
$(NLTIME): newlib/*.c newlib/*.h newlib/compat/*.h newlib/sys/*.h
	$(MAKE) -C newlib OUT=../$(OUT)/newlib
$(OUT):
	mkdir -p $(OUT)

# ---- browser build (WebAssembly) with the system clang + Ubuntu's wasm32 libraries:
#      apt install wasi-libc libc++-18-dev-wasm32 libc++abi-18-dev-wasm32 libclang-rt-18-dev-wasm32
WASM_CXX   ?= clang++
WASM_FLAGS := --target=wasm32-wasi --sysroot=/usr -std=gnu++17 -Oz -fno-exceptions \
              -DSIM_WASM -DSIM_NO_THREADS -DARDUINO=10819 -DARDUINOJSON_ENABLE_PROGMEM=0 \
              -Ishim -I$(FW) -I$(AJ) -Wno-unused-function
WASM_OUT   := ../../docs/demo/ceilingclock.wasm

wasm: $(WASM_OUT)
WASM_NL    := mktime lcltime_r gmtime_r tzset_r tzset tzcalc_limits gettzinfo tzvars month_lengths nl_lock
$(WASM_OUT): $(FW)/*.cpp $(FW)/*.h sim_hw.cpp sim_wasm.cpp shim/*.h newlib/*.c newlib/*.h
	mkdir -p $(OUT)/wasm $(dir $(WASM_OUT))
	for f in $(FW_SRC); do $(WASM_CXX) $(WASM_FLAGS) -c $(FW)/$$f.cpp -o $(OUT)/wasm/$$f.o || exit 1; done
	for f in $(WASM_NL); do $(WASM_CXX:clang++=clang) --target=wasm32-wasi --sysroot=/usr -Oz -w -Inewlib -Inewlib/compat \
	  -include newlib/nl_rename.h -c newlib/$$f.c -o $(OUT)/wasm/nl_$$f.o || exit 1; done
	$(WASM_CXX) $(WASM_FLAGS) -c sim_hw.cpp -o $(OUT)/wasm/sim_hw.o
	$(WASM_CXX) $(WASM_FLAGS) -c sim_wasm.cpp -o $(OUT)/wasm/sim_wasm.o
	$(WASM_CXX) $(WASM_FLAGS) -mexec-model=reactor $(OUT)/wasm/*.o -lc++abi -Wl,--strip-all -o $@
	python3 make_demo_page.py

run: all
	./$(OUT)/ceilingclock-sim

clean:
	rm -rf $(OUT)
.PHONY: all run clean wasm check-src
