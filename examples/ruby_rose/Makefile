.PHONY: default
default: all

# SOURCE FILES

%.xz: %
	xz --compress --keep --force $<

%.blend: %.blend.xz
	xz --decompress --keep --force $<
	touch $@

# EGG FILES

ruby_mesh.egg: ruby.blend
	blend2egg --output $@ --render rp $<

ruby_anim.egg: ruby.blend
	blend2egg --output $@ --export animation $<

EGG_FILES = ruby_mesh.egg ruby_anim.egg

# GLTF FILES

ruby_mesh.gltf: ruby.blend
	blend2gltf --output $@ --render rp $<

ruby_anim.gltf: ruby.blend
	blend2gltf --output $@ --export animation $<

GLTF_FILES = ruby_mesh.gltf ruby_anim.gltf

# RULES

egg: $(EGG_FILES)

gltf: $(GLTF_FILES)

all: $(EGG_FILES) $(GLTF_FILES)

# packs back modified source files
pack: ruby.blend.xz rubyAnimated002.fbx.xz

clean:
	rm -fv $(EGG_FILES) $(GLTF_FILES) ruby.blend
