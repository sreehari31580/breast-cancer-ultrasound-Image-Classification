from __future__ import annotations
import numpy as np
import torch
import torch.nn as nn
import cv2


class GradCAM:
	def __init__(self, model: nn.Module, target_layer_name: str = "layer4"):
		self.model = model
		self.model.eval()
		self.target_layer = self._get_layer(target_layer_name)
		self.activations = None
		self.gradients = None
		self._register_hooks()

	def _get_layer(self, name: str):
		# Works for torchvision resnets: layer1..layer4
		mod = self.model
		for part in name.split('.'):
			mod = getattr(mod, part)
		return mod

	def _register_hooks(self):
		def fwd_hook(_, __, output):
			self.activations = output.detach()

		def bwd_hook(_, grad_in, grad_out):
			# grad_out is a tuple; first element corresponds to output grad
			self.gradients = grad_out[0].detach()

		self.target_layer.register_forward_hook(fwd_hook)
		self.target_layer.register_full_backward_hook(bwd_hook)

	def __call__(self, x: torch.Tensor, class_idx: int | None = None) -> np.ndarray:
		self.model.zero_grad()
		logits = self.model(x)
		if class_idx is None:
			class_idx = int(torch.argmax(logits, dim=1).item())
		score = logits[:, class_idx]
		score.backward(retain_graph=True)

		# Global average pool gradients to get weights
		weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)  # [B, C, 1, 1]
		cam = torch.sum(weights * self.activations, dim=1)  # [B, H, W]
		cam = torch.relu(cam)

		# Normalize each map to [0,1]
		cam_min = cam.amin(dim=(1, 2), keepdim=True)
		cam_max = cam.amax(dim=(1, 2), keepdim=True)
		cam = (cam - cam_min) / (cam_max - cam_min + 1e-8)
		cam_np = cam[0].cpu().numpy()
		return cam_np


def overlay_heatmap(image_rgb: np.ndarray, heatmap: np.ndarray, alpha: float = 0.4) -> np.ndarray:
	h, w = image_rgb.shape[:2]
	heatmap_resized = cv2.resize(heatmap, (w, h))
	heatmap_uint8 = np.uint8(255 * heatmap_resized)
	heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
	heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)
	if image_rgb.max() <= 1:
		base = (image_rgb * 255).astype(np.uint8)
	else:
		base = image_rgb.astype(np.uint8)
	overlay = cv2.addWeighted(base, 1 - alpha, heatmap_color, alpha, 0)
	return overlay
