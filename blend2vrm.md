blend2vrm
==========

BLEND to [VRM](https://vrm.dev/) converter.


Features
--------

* Export full VRM meta info
* Export VRM materials and shaders
* Export shape keys as VRM blend shapes
* Pose freeze
* Pack textures including the model's thumbnail


Requirements
------------

* python-blender (2.81+) (Blender as Python module) or Blender's Python


VRM meta info template
----------------------

Save it as "VRM.ini" text block inside Blender:

```
[meta]
title = Model name
version = Model version
author = Author name
contactInformation = Author contact
reference = http://example.com/

allowedUserName = OnlyAuthor
#allowedUserName = ExplicitlyLicensedPerson
#allowedUserName = Everyone

violentUssageName = Disallow
#violentUssageName = Allow

sexualUssageName = Disallow
#sexualUssageName = Allow

commercialUssageName = Disallow
#commercialUssageName = Allow

#otherPermissionUrl = http://example.com/

licenseName = Redistribution_Prohibited
#licenseName = CC0
#licenseName = CC_BY
#licenseName = CC_BY_NC
#licenseName = CC_BY_SA
#licenseName = CC_BY_NC_SA
#licenseName = CC_BY_ND
#licenseName = CC_BY_NC_ND
#licenseName = Other
#otherLicenseUrl = http://example.com/
```


Exporting models
----------------

```
blend2vrm --output x.vrm x.blend
```
