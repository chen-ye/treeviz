import { ScatterplotLayer } from '@deck.gl/layers';
import type { ScatterplotLayerProps } from '@deck.gl/layers';
import type { Texture } from '@luma.gl/core';
import type { DefaultProps } from '@deck.gl/core';

export type PhenologyLayerProps<DataT = any> = _PhenologyLayerProps & ScatterplotLayerProps<DataT>;

type _PhenologyLayerProps = {
  uAtlas?: Texture | null;
  uTime?: number;
  uAtlasHeight?: number;
  getSpeciesIndex?: (d: any) => number;
};

// Custom Fragment Shader
const fragmentShader = `
#version 300 es
precision highp float;

uniform sampler2D uAtlas;
uniform float uTime;   // Day of Year (0..365)
uniform float uAtlasHeight; // Number of rows in atlas

in vec2 vTexCoord;
in vec3 vPosition;
in vec4 vColor; // Original instance color (unused if overriding)
in float vInstanceSpecies; // Row index in atlas

out vec4 fragColor;

void main() {
  // Scatterplot circle logic (distance from center)
  vec2 geometry = vTexCoord * 2.0 - 1.0;
  float dist = length(geometry);
  float alpha = smoothstep(1.0, 0.8, dist);
  if (dist > 1.0) {
    discard;
  }

  // Phenology Lookup
  // uTime is 1..365. Normalize to 0..1
  float u = clamp(uTime / 365.0, 0.0, 1.0);

  // vInstanceSpecies is integer index (0, 1, 2...).
  // Map to center of pixel row: (index + 0.5) / height
  float v = (vInstanceSpecies + 0.5) / uAtlasHeight;

  vec4 phenoColor = texture(uAtlas, vec2(u, v));

  // Apply alpha for circle shape
  fragColor = vec4(phenoColor.rgb, alpha);
}
`;

export class PhenologyLayer<DataT = any, ExtraPropsT = {}> extends ScatterplotLayer<DataT, _PhenologyLayerProps & ExtraPropsT> {
  getShaders() {
    const shaders = super.getShaders();
    return {
      ...shaders,
      fs: fragmentShader,
      inject: {
        'vs:#decl': `
          in float instanceSpecies;
          out float vInstanceSpecies;
        `,
        'vs:#main-end': `
          vInstanceSpecies = instanceSpecies;
        `
      }
    };
  }

  initializeState() {
    super.initializeState();
    this.getAttributeManager()?.add({
      instanceSpecies: {
        size: 1,
        accessor: 'getSpeciesIndex',
        type: 'float32'
      }
    });
  }
}

PhenologyLayer.layerName = 'PhenologyLayer';
PhenologyLayer.defaultProps = {
  ...ScatterplotLayer.defaultProps,
  uAtlas: null,
  uTime: 0,
  uAtlasHeight: 1,
  getSpeciesIndex: { type: 'accessor', value: 0 }
} as DefaultProps<PhenologyLayerProps>;
