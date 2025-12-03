import { ScatterplotLayer } from '@deck.gl/layers';
import type { ScatterplotLayerProps } from '@deck.gl/layers';
import type { Texture } from '@luma.gl/core';
import type { DefaultProps, UpdateParameters } from '@deck.gl/core';

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
          in float instanceSpecies;
          out float vInstanceSpecies;
        `,
        'vs:#main-end': `
          vInstanceSpecies = instanceSpecies;
        `,
        'fs:#decl': `
          uniform sampler2D uAtlas;
          uniform float uTime;
          uniform float uAtlasHeight;
          in float vInstanceSpecies;
        `,
        'fs:DECKGL_FILTER_COLOR': `
          // Lookup phenology color from atlas texture and override RGB
          float u = clamp(uTime / 365.0, 0.0, 1.0);
          float v = (vInstanceSpecies + 0.5) / uAtlasHeight;
          vec3 pheno = texture(uAtlas, vec2(u, v)).rgb;
          color = vec4(pheno, color.a);
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

  updateState(params: UpdateParameters<this>) {
    super.updateState(params);

    const {props} = params;

    // Minimal model interface for the methods we use on the luma Model
    type LumaModelLike = {
      setUniforms?: (uniforms: Record<string, unknown>) => void;
      setBindings?: (bindings: Record<string, Texture | null>) => void;
    };

    // Ensure the model bindings/uniforms are updated so the sampler is bound
    const model = ((this.state)?.model) as LumaModelLike | undefined;
    if (!model) return;

    // Set texture binding for sampler uniform if available
    const bindings: Record<string, Texture | null> = {};
    if (props.uAtlas) {
      bindings.uAtlas = props.uAtlas;
    }

    // Update uniforms (uTime, uAtlasHeight)
    if (typeof model.setUniforms === 'function') {
      model.setUniforms({
        uTime: props.uTime ?? 0,
        uAtlasHeight: props.uAtlasHeight ?? 1
      });
    }

    // setBindings may exist on luma Model; use if available
    if (Object.keys(bindings).length > 0 && typeof model.setBindings === 'function') {
      model.setBindings(bindings);
    }
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
