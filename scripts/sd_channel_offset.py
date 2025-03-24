import torch
import modules.scripts as scripts
import gradio as gr
import modules.shared as shared
import modules.processing as processing
from modules.shared import opts
from modules.rng import ImageRNG as OriginalImageRNG
from modules import script_callbacks

rng_next = OriginalImageRNG.next

class Script(scripts.Script):

    def title(self):
        return  "Channel Offset Extension"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def on_app_started(self, block, app):
        OriginalImageRNG.next = patch_next

    def ui(self, is_img2img):

        def get_slider(min, max, value, step, label):
            return gr.Slider(
                minimum=min,
                maximum=max,
                value=value,
                step=step,
                label=label
            )

        with gr.Accordion("Channel Offset", open=False):
            self.enabled_control = gr.Checkbox(label="Enabled", value=True)
            gr.Markdown("Modify latent noise offset globally or per channel. Some models & prompts may be sensitive to  changes over 0.1")
            with gr.Row():
                self.drop_mean_post_control = gr.Checkbox(label="Drop Mean After Offset", value=False)
                self.save_control = gr.Checkbox(label="Save Metadata", value=True)
                clear_button = gr.Button("Clear Offsets")

            self.global_offset_control = get_slider(-0.5, 0.5, 0.0, 0.005, "Global Noise Offset")
            gr.Markdown("      ============= Primary Channels ================") #surely there is a prettier way to do this

            self.channel_sliders = []
            for i in range(4):
                slider = get_slider(-0.5, 0.5, 0.0, 0.005, f"Channel {i+1} Offset")
                self.channel_sliders.append(slider)

            with gr.Accordion("Additional Channels (uncommon)", open=False):
                for i in range(4):
                    slider = get_slider(-0.5, 0.5, 0.0, 0.005,f"Channel {i+5} Offset")
                    self.channel_sliders.append(slider)

            with gr.Accordion("Experimental / Tinker", open=False):
                with gr.Row():
                    self.drop_mean_control = gr.Checkbox(label="Drop Mean Before Offset", value=False)
                    self.drop_channel_means_control = gr.Checkbox(label="Drop Channel Means Before Offset", value=False)
                    self.first_step_control = gr.Checkbox(label="Apply only to first step", value=True)

            self.update_button = gr.Button("Update Values", visible=False)

        def clear_offsets():
            return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        clear_button.click(
            fn=clear_offsets,
            inputs=[],
            outputs=[self.global_offset_control] + self.channel_sliders
        )

        self.infotext_fields = [
            (self.drop_mean_control, "drop_mean"),
            (self.drop_channel_means_control, "drop_channel_means"),
            (self.drop_mean_post_control, "drop_mean_post"),
            (self.global_offset_control, "offset_global"),
            (self.first_step_control, "offset_first_only")
        ]

        for i, slider in enumerate(self.channel_sliders):
            self.infotext_fields.append((slider, f"offset_channel{i+1}"))

        self.paste_field_names = [name for _, name in self.infotext_fields]

        global _channel_offset_instance
        _channel_offset_instance = self

        return [self.enabled_control, self.drop_mean_control, self.drop_channel_means_control, self.drop_mean_post_control, self.save_control, self.first_step_control, self.global_offset_control] + self.channel_sliders


    def process(self, p, is_enabled, drop_mean, drop_channel_means, drop_mean_post, save_meta, first_only, global_offset, *channel_sliders):
        channel_offsets = list(channel_sliders)

        # Store values in options
        opts.lpco_is_enabled = is_enabled
        opts.lpco_drop_mean = drop_mean
        opts.lpco_drop_channel_means = drop_channel_means
        opts.lpco_drop_mean_post = drop_mean_post
        opts.lpco_global_offset = global_offset
        opts.lpco_channel_offsets = channel_offsets
        opts.lpco_first_only = first_only

        if OriginalImageRNG.next != patch_next:
            OriginalImageRNG.next = patch_next

        if save_meta and is_enabled:
            if drop_mean:
                p.extra_generation_params["drop_mean"] = drop_mean
            if drop_channel_means:
                p.extra_generation_params["drop_channel_means"] = drop_channel_means
            if drop_mean_post:
                p.extra_generation_params["drop_mean_post"] = drop_mean_post
            if not first_only: # default is true, so we only store false.
                p.extra_generation_params["offset_first_only"] = first_only
            if abs(global_offset) > 1e-8:
                p.extra_generation_params["offset_global"] = global_offset
            for i in range(8):
                if abs(channel_offsets[i]) > 1e-8:
                    p.extra_generation_params[f"offset_channel{i+1}"] = channel_offsets[i]

        return p


def patch_next(self):
    apply_offset = self.is_first or not opts.lpco_first_only
    noise = rng_next(self)
    if noise is None or not apply_offset or not opts.lpco_is_enabled:
        return noise

    drop_mean = opts.lpco_drop_mean
    drop_channel_means = opts.lpco_drop_channel_means
    drop_mean_post = opts.lpco_drop_mean_post
    global_offset = opts.lpco_global_offset
    channel_offsets = opts.lpco_channel_offsets or []

    if drop_mean:
        noise -= noise.mean()

    if drop_channel_means:
        channel_means = noise.mean(dim=(0, 2, 3), keepdim=True)
        noise -= channel_means

    if abs(global_offset) > 1e-8:
        noise += global_offset

    if channel_offsets:
        channel_count = noise.shape[1]
        relevant = channel_offsets[:channel_count]
        offset_tensor = torch.tensor(relevant, device=noise.device, dtype=noise.dtype).view(1, -1, 1, 1)
        noise += offset_tensor

    if drop_mean_post:
        noise -= noise.mean()

    return noise


def on_infotext_pasted(infotext, params):
    '''
     we only store non-zero offset values in meta data.
     but we want to set things to zero when png info is applied,
     so we do that here, setting anything not included in meta to its default value.
    '''

    if not "drop_mean" in params:
        params["drop_mean"] = False

    if not "drop_channel_means" in params:
        params["drop_channel_means"] = False

    if not "drop_mean_post" in params:
        params["drop_mean_post"] = False

    if not "offset_first_only" in params:
        params["offset_first_only"] = True

    if not "global_offset" in params:
        params["global_offset"] = 0.0


    for i in range(8):
        if not f"offset_channel{i+1}" in params:
            params[f"offset_channel{i+1}"] = 0.0


script_callbacks.on_infotext_pasted(on_infotext_pasted)