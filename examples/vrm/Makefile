.PHONY: default
default: all

# SOURCE FILES

%.xz: %
	xz --compress --keep --force $<

%.blend: %.blend.xz
	xz --decompress --keep --force $<
	touch $@

# VRM FILES

latifa_v2.vrm: latifa_v2.blend
	blend2vrm --output $@ $<

VRM_FILES = latifa_v2.vrm

# RULES

vrm: $(VRM_FILES)

all: $(VRM_FILES)

# packs back modified source files
pack: latifa_v2.blend.xz Latifa_V2_Sketchfab.fbx.xz

clean:
	rm -fv $(VRM_FILES) latifa_v2.blend
