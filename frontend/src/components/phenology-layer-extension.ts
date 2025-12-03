import { LayerExtension } from '@deck.gl/core';
import type { ShaderModule } from '@luma.gl/shadertools';
import type { Texture } from '@luma.gl/core';

// Props that can be passed to layers using the PhenologyExtension
export type PhenologyExtensionProps = {
  phenologyAtlas?: Texture | null;
  phenologyTime?: number;
  phenologyAtlasHeight?: number;
  getPhenologySpeciesIndex?: (d: any) => number;
  getPhenologyAdjustmentDays?: (d: any) => number;
};

// Define the UBO structure
type PhenologyUniforms = {
  time: number;
  atlasHeight: number;
};

// Create the shader module with UBO
const phenologyUniforms = {
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
  uniformTypes: {
    time: 'f32',
    atlasHeight: 'f32'
  }
} as const satisfies ShaderModule<PhenologyUniforms>;

/**
 * Layer extension that adds phenology visualization using a texture atlas.
 *
 * This extension can be applied to any deck.gl layer (including composite layers like GeoJsonLayer)
 * to add time-based phenology coloring using a species index and texture atlas lookup.
 *
 * Features:
 * - Species-specific phenology via atlas texture lookup
 * - Per-tree timeline adjustment based on microclimate (elevation, urban heat island)
 *
 * Usage:
 * ```ts
 * new ScatterplotLayer({
 *   data,
 *   getPhenologySpeciesIndex: d => d.speciesId,
 *   getPhenologyAdjustmentDays: d => d.adjustment_days,
 *   phenologyAtlas: texture,
 *   phenologyTime: dayOfYear,
 *   phenologyAtlasHeight: 256,
 *   extensions: [new PhenologyExtension()]
 * })
 * ```
 */
export class PhenologyExtension extends LayerExtension<PhenologyExtensionProps> {
  getShaders() {
    return {
      modules: [phenologyUniforms],
      inject: {
        'vs:#main-end': `
          vPhenologySpecies = instancePhenologySpecies;
          vPhenologyAdjustment = instancePhenologyAdjustment;
        `,
        'fs:DECKGL_FILTER_COLOR': `
          // Apply per-tree adjustment to the timeline
          // Negative adjustment = earlier phenology (sample later in atlas)
          // Positive adjustment = later phenology (sample earlier in atlas)
          float adjustedTime = phenology.time - vPhenologyAdjustment;

          // Wrap around year boundaries (0-365)
          adjustedTime = mod(adjustedTime + 365.0, 365.0);

          // Lookup phenology color from atlas texture using adjusted time
          float u = clamp(adjustedTime / 365.0, 0.0, 1.0);
          float v = (vPhenologySpecies + 0.5) / phenology.atlasHeight;
          vec3 phenoColor = texture(phenologyAtlas, vec2(u, v)).rgb;
          color = vec4(phenoColor, color.a);
        `
      }
    };
  }

  initializeState() {
    // Add the species index and adjustment days attributes
    (this as any).getAttributeManager()?.add({
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

  updateState(params: any) {
    const { props } = params;

    // Get all models from the layer
    const models = (this as any).getModels?.();
    if (!models || models.length === 0) return;

    for (const model of models) {
      // Update UBO with time and atlasHeight
      if (model.shaderInputs) {
        model.shaderInputs.setProps({
          phenology: {
            time: props.phenologyTime ?? 0,
            atlasHeight: props.phenologyAtlasHeight ?? 1
          } as PhenologyUniforms
        });
      }

      // Set texture binding for the atlas sampler
      if (props.phenologyAtlas && model.bindings) {
        model.bindings.phenologyAtlas = props.phenologyAtlas;
      }
    }
  }

  getSubLayerProps() {
    // Pass phenology props down to any sublayers
    return {
      phenologyAtlas: (this as any).props.phenologyAtlas,
      phenologyTime: (this as any).props.phenologyTime,
      phenologyAtlasHeight: (this as any).props.phenologyAtlasHeight,
      getPhenologySpeciesIndex: (this as any).props.getPhenologySpeciesIndex,
      getPhenologyAdjustmentDays: (this as any).props.getPhenologyAdjustmentDays
    };
  }
}
