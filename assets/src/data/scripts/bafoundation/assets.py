# Copyright (c) 2011-2019 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""Functionality related to cloud based assets."""

from __future__ import annotations

from typing import TYPE_CHECKING
from enum import Enum

from bafoundation import entity

if TYPE_CHECKING:
    pass


class AssetPackageFlavor(Enum):
    """Flavors for asset package outputs for different platforms/etc."""

    # DXT3/DXT5 textures
    DESKTOP = 'desktop'

    # ASTC textures
    MOBILE = 'mobile'


class AssetType(Enum):
    """Types for individual assets within a package."""
    TEXTURE = 'texture'
    SOUND = 'sound'
    DATA = 'data'


class AssetInfo(entity.CompoundValue):
    """Info for a specific asset file in a package."""
    filehash = entity.Field('h', entity.StringValue())
    fileext = entity.Field('e', entity.StringValue())


class AssetPackageFlavorManifestValue(entity.CompoundValue):
    """A manifest of asset info for a specific flavor of an asset package."""
    assets = entity.CompoundDictField('a', str, AssetInfo())


class AssetPackageFlavorManifest(entity.EntityMixin,
                                 AssetPackageFlavorManifestValue):
    """A self contained AssetPackageFlavorManifestValue."""


class AssetPackageBuildState(entity.Entity):
    """Contains info about an in-progress asset cloud build."""
    in_progress_builds = entity.ListField('b', entity.StringValue())
