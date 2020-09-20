.PHONY: default
default: all

# EGG FILES

snake_mesh.b2e.egg: snake.blend
	blend2egg --output $@ --render rp $<

snake_anim.b2e.egg: snake.blend
	blend2egg --output $@ --export animation $<

EGG_FILES = \
	snake_mesh.b2e.egg \
	snake_anim.b2e.egg

# GLTF FILES

# blend -> gltf
snake_mesh.b2g.gltf: snake.blend
	blend2gltf --output $@ --render rp $<

# blend -> gltf -> bam
snake_mesh.b2g.bam: snake_mesh.b2g.gltf
	gltf2bam $< $@

# blend -> gltf -> bam -> egg
snake_mesh.b2g.egg: snake_mesh.b2g.bam
	bam2egg $< -o $@

# blend -> gltf
snake_anim.b2g.gltf: snake.blend
	blend2gltf --output $@ --export animation $<

# blend -> gltf -> bam
snake_anim.b2g.bam: snake_anim.b2g.gltf
	gltf2bam $< $@

# blend -> gltf -> bam -> egg
snake_anim.b2g.egg: snake_anim.b2g.bam
	bam2egg $< -o $@

GLTF_FILES = \
	snake_mesh.b2g.gltf \
	snake_anim.b2g.gltf

GLTF_TEST_FILES = \
	snake_mesh.b2g.bam \
	snake_mesh.b2g.egg \
	snake_anim.b2g.bam \
	snake_anim.b2g.egg

# RULES

egg: $(EGG_FILES)

gltf: $(GLTF_FILES)
gltf_test: $(GLTF_TEST_FILES)

all: $(EGG_FILES) $(GLTF_FILES)
test: all gltf_test

clean:
	rm -fv $(EGG_FILES) $(GLTF_FILES) $(GLTF_TEST_FILES)
