.PHONY: default
default: all

# SOURCE FILES

%.xz: %
	xz --compress --keep --force $<

%.blend: %.blend.xz
	xz --decompress --keep --force $<
	touch $@

# EGG FILES

ruby.egg: ruby.blend
	blend2egg --output $@ --render rp $<

ruby_anim.egg: ruby.blend
	blend2egg --output $@ --export animation $<

EGG_FILES = ruby.egg ruby_anim.egg

egg: $(EGG_FILES)

# GLTF FILES

ruby.gltf: ruby.blend
	blend2gltf --output $@ --render rp $<

ruby_anim.gltf: ruby.blend
	blend2gltf --output $@ --export animation $<

GLTF_FILES = ruby.gltf ruby_anim.gltf

# RULES

gltf: $(GLTF_FILES)

all: $(EGG_FILES) $(GLTF_FILES)

# packs back modified source files
pack: ruby.blend.xz rubyAnimated002.fbx.xz

clean:
	rm -fv $(EGGs) $(GLTFs)
