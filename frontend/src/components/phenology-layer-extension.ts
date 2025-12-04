import { LayerExtension } from '@deck.gl/core';
import type { Layer, UpdateParameters } from '@deck.gl/core';
import type { ShaderModule } from '@luma.gl/shadertools';
import type { Texture } from '@luma.gl/core';
import type { Model } from '@luma.gl/engine';
import type { ScatterplotLayer } from '@deck.gl/layers';

export type PhenologyExtensionProps = {
  phenologyAtlas?: Texture | null;
  phenologyTime?: number;
  phenologyAtlasHeight?: number;
  getPhenologySpeciesIndex?: (d: any) => number;
  getPhenologyAdjustmentDays?: (d: any) => number;
};

/**
 * Defines the Uniform Buffer Object (UBO) structure.
 * These keys must match the 'uniformTypes' definition and the GLSL struct.
 */
type PhenologyUniforms = {
  time: number;
  atlasHeight: number;
};

/**
 * The Shader Module definition.
 * * In luma.gl v9:
 * 1. 'uniformTypes' defines the UBO layout.
 * 2. The module name ('phenology') becomes the key used in 'model.shaderInputs.setProps'.
 */
const phenologyModule = {
  name: 'phenology',
  vs: `
    uniform phenologyUniforms {
      float time;
      float atlasHeight;
    } phenology;

    in float instancePhenologySpecies;
    in float instancePhenologyAdjustment;
    out float vPhenologySpecies;
    out float vPhenologyAdjustment;
  `,
  fs: `
    uniform phenologyUniforms {
      float time;
      float atlasHeight;
    } phenology;

    uniform sampler2D phenologyAtlas;

    in float vPhenologySpecies;
    in float vPhenologyAdjustment;
  `,
  // strict matching of keys to the UBO float/int types
  uniformTypes: {
    time: 'f32',
    atlasHeight: 'f32'
  }
} as const satisfies ShaderModule<PhenologyUniforms>;

/**
 * Layer extension that adds phenology visualization using a texture atlas.
 */
export class PhenologyExtension extends LayerExtension<PhenologyExtensionProps> {
  getShaders() {
    return {
      modules: [phenologyModule],
      inject: {
        'vs:#main-end': `
          vPhenologySpecies = instancePhenologySpecies;
          vPhenologyAdjustment = instancePhenologyAdjustment;
        `,
        'fs:DECKGL_FILTER_COLOR': `
          // Apply per-tree adjustment to the timeline
          float adjustedTime = phenology.time - vPhenologyAdjustment;

          // Wrap around year boundaries (0-365)
          adjustedTime = mod(adjustedTime + 365.0, 365.0);

          // Lookup phenology color from atlas texture
          // Note: Standard UV coords are 0..1
          float u = clamp(adjustedTime / 365.0, 0.0, 1.0);

          // Atlas rows correspond to species.
          // We add 0.5 to sample the center of the pixel row.
          float v = (vPhenologySpecies + 0.5) / phenology.atlasHeight;

          vec3 phenoColor = texture(phenologyAtlas, vec2(u, v)).rgb;

          // Mix or replace logic - here we assume the atlas color
          // modulates the existing alpha, or replaces the RGB entirely.
          color = vec4(phenoColor, color.a);
        `
      }
    };
  }

  initializeState() {
    // We cast to any/ScatterplotLayer to access getAttributeManager.
    // In v9, standard attributes added here are automatically instanced
    // because the layer renders one instance per data row.
    (this as unknown as ScatterplotLayer<PhenologyExtensionProps>).getAttributeManager()?.add({
      instancePhenologySpecies: {
        size: 1,
        accessor: 'getPhenologySpeciesIndex',
        type: 'float32'
      },
      instancePhenologyAdjustment: {
        size: 1,
        accessor: 'getPhenologyAdjustmentDays',
        type: 'float32',
        defaultValue: 0
      }
    });
  }

  updateState(params: UpdateParameters<Layer<PhenologyExtensionProps>>) {
    const { props } = params;

    // In deck.gl v9, models are retrieved via getModels()
    // We cast to any because getModels is not strictly typed on the generic Layer
    const models = (this as any).getModels() as Model[];
    if (!models) return;

    for (const model of models) {
      // 1. Update UBO Uniforms via ShaderInputs
      // The key 'phenology' matches the module.name defined above
      model.shaderInputs.setProps({
        phenology: {
          time: props.phenologyTime ?? 0,
          atlasHeight: props.phenologyAtlasHeight ?? 1
        }
      });

      // 2. Update Texture Bindings
      // In luma.gl v9, samplers are set via setBindings, not shaderInputs
      if (props.phenologyAtlas) {
        model.setBindings({
          phenologyAtlas: props.phenologyAtlas
        });
      }
    }
  }

  getSubLayerProps() {
    const {
      phenologyAtlas,
      phenologyTime,
      phenologyAtlasHeight,
      getPhenologySpeciesIndex,
      getPhenologyAdjustmentDays
    } = (this as any).props;

    return {
      phenologyAtlas,
      phenologyTime,
      phenologyAtlasHeight,
      getPhenologySpeciesIndex,
      getPhenologyAdjustmentDays
    };
  }
}
