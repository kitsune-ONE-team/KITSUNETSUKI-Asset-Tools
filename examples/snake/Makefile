.PHONY: default
default: all

# EGG FILES

snake.egg: snake.blend
	blend2egg --output $@ --render rp $<

snake_anim.egg: snake.blend
	blend2egg --output $@ --export animation $<

EGG_FILES = snake.egg snake_anim.egg

# GLTF FILES

snake.gltf: snake.blend
	blend2gltf --output $@ --render rp $<

snake_anim.gltf: snake.blend
	blend2gltf --output $@ --export animation $<

snake_gltf.bam: snake.gltf
	gltf2bam $< $@

snake_gltf.egg: snake_gltf.bam
	bam2egg $< -o $@

GLTF_FILES = snake.gltf snake_anim.gltf
GLTF_TEST_FILES = snake_gltf.bam snake_gltf.egg

# RULES

egg: $(EGG_FILES)

gltf: $(GLTF_FILES)

gltf_test: $(GLTF_TEST_FILES)

all: $(EGG_FILES) $(GLTF_FILES)

clean:
	rm -fv $(EGG_FILES) $(GLTF_FILES) $(GLTF_TEST_FILES)
