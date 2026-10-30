# PC simulator for the Ceiling Clock firmware.
# Compiles the real firmware sources (../src) against stand-ins for the ESP32 hardware in shim/.
# Needs ArduinoJson: run `pio pkg install` (or one `pio run`) in ../ first so .pio/libdeps exists.
FW  := ../src
AJ  := ../.pio/libdeps/esp32s3/ArduinoJson/src
CXX ?= g++
CXXFLAGS := -std=gnu++17 -O1 -g -Wall -Wno-unused-variable -Wno-unused-function -pthread \
            -Ishim -I$(FW) -I$(AJ) -DARDUINO=10819 -DARDUINOJSON_ENABLE_PROGMEM=0
OUT := build

all: $(OUT)/ceilingclock-sim

$(OUT)/main.o: $(FW)/main.cpp $(FW)/*.h shim/*.h | $(OUT)
	$(CXX) $(CXXFLAGS) -Dtime=sim_time -c $< -o $@
$(OUT)/settings.o: $(FW)/settings.cpp $(FW)/settings.h shim/*.h | $(OUT)
	$(CXX) $(CXXFLAGS) -c $< -o $@
$(OUT)/sim_hw.o: sim_hw.cpp shim/*.h shim/glcdfont.c | $(OUT)
	$(CXX) $(CXXFLAGS) -c $< -o $@
$(OUT)/sim_main.o: sim_main.cpp | $(OUT)
	$(CXX) $(CXXFLAGS) -c $< -o $@
$(OUT)/ceilingclock-sim: $(OUT)/main.o $(OUT)/settings.o $(OUT)/sim_hw.o $(OUT)/sim_main.o
	$(CXX) $(CXXFLAGS) $^ -o $@
$(OUT):
	mkdir -p $(OUT)

run: all
	./$(OUT)/ceilingclock-sim

clean:
	rm -rf $(OUT)
.PHONY: all run clean
