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

export class PhenologyLayer<DataT = any, ExtraPropsT = {}> extends ScatterplotLayer<DataT, _PhenologyLayerProps & ExtraPropsT> {
  getShaders() {
    const shaders = super.getShaders();
    return {
      ...shaders,
      inject: {
        'vs:#decl': `
          uniform sampler2D uAtlas;
          uniform float uTime;
          uniform float uAtlasHeight;
          
          in float instanceSpecies;
          out float vInstanceSpecies;
        `,
        'vs:#main-end': `
          vInstanceSpecies = instanceSpecies;
        `,
        'vs:DECKGL_FILTER_COLOR': `
          // Phenology color lookup from atlas
          float u = clamp(uTime / 365.0, 0.0, 1.0);
          float v = (vInstanceSpecies + 0.5) / uAtlasHeight;
          vec4 phenoColor = texture(uAtlas, vec2(u, v));
          color = phenoColor;
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
