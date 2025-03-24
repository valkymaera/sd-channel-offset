# sd-channel-offset
Automatic1111 extension allowing an offset to be applied to latent noise per-channel before generation

About:
latent noise channels don't represent pixel color values, not really. I mean I think they're related to the mean color values of certain images in training, but the result of that is the channels are tied to concepts more than colors in the output (although they do influence hue). For this reason, different models may respond to channels differently based on how they were trained. Prompts will also change how much influence a channel has as modifying them will bring out more features within their concept space.

However there are some neat domains that tend to be shared among models. Notably, channel 1 tends to influence concepts related to being enclosed, shaded, and/or dark, among other things, allowing us to draw out those features in a way that can be challenging from tokens and emphasis alone.

Consider the following alien landscape: 
![d](https://github.com/user-attachments/assets/8c7af040-05ab-4dd2-bc55-8103c7d808bd)

if we crank channel 1 very low, we can see the space become warmer, shaded, and more enclosed.
![a](https://github.com/user-attachments/assets/353efe3e-0a1d-42e3-9cb5-42db14673994)

if we crank channel 1 very high, we see it instead become open, exposed, and brighter.
![2](https://github.com/user-attachments/assets/6faf03fa-20b0-40f3-8de2-c97d78619e3f)


By tinkering with various channels, we can fine tune conceptual features (albeit sometimes a little blindly), often enhancing them beyond what we usually get out of tokens and emphasis alone.

![1](https://github.com/user-attachments/assets/7aaf3e19-537b-4680-aaea-91e38fd1a07c)
![5](https://github.com/user-attachments/assets/4914121d-8166-467b-b95c-3d300191b4ed)

Important notes:
* Offset is applied each time noise is applied, meaning for Euler/ ancestral samplers that fetch noise every step, smaller values will be much more impactful. 
* Channels 5 through 8 are not generally used though supposedly some models can support up to 8 channels, so I included it.
* This extension works by intercepting rng.py ImageRNG.next() and adding values into the result. Other extensions that intercept it might prevent it from working, or vice versa.
* Different models may respond differently or be more/less sensitive to the influence of each channel

UI:
Drop Mean Before Offset: this subtracts the mean value from the noise before doing anything else, "centering" it. 
Drop Channel Means Before Offset: this subtracts the mean value for each channel separately, before applying offsets. 
Both of these can help keep offset changes in a "healthy" range by reducing extremes, but the effect is usually subtle, and I've considered removing them.
I left them in for tinkerers like myself.

Drop Mean After Offset: this subtracts the final mean value from the noise, which can have significant impact.
This will often bring the composition closer to the original while keeping the relative weight adjustments of each channel, but you will often lose some of the intensity of the offsets, as well as their negative or positive value based on the value of the mean.
It can be useful for restoring elements of the original output that you prefer, but it's similar to centering the sliders along their total average (while also considering inherent noise values). 
If you keep the sliders at zero this is basically the same thing as Drop Mean Before Offset, because it's still dropping whatever mean value is there.

original:
![k1](https://github.com/user-attachments/assets/3c8bb2ed-6be0-42bf-8343-0bc323d77349)

after offset tinkering:
![k2](https://github.com/user-attachments/assets/4f348a9e-2686-43e0-b282-11ec9a8a21e3)

droping mean:
![k3](https://github.com/user-attachments/assets/bc9f3445-ab70-4e5a-b788-dd708f32b0ef)

The above samples use SDXL model "quadpipe"
https://civitai.com/models/996342/quadpipe-or-qp


Channel Effects:
The effects of each channel vary per model and prompt (for example, channel 1 will have a stronger 'darkening' effect if you include tokens related to darkness in your prompt), but tend to have some overlap in effect on style and color influence.  













