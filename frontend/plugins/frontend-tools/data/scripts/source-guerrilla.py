import obspython as obs

# ------------------------------------------------------------
# Source Guerrilla
#
# Aligns every source across all scenes to a single "Universal
# Source" (default name: "Harmony of all things"). When the
# alignment runs, the position, scale, rotation, alignment,
# bounding box and crop of the universal source are copied onto
# every other scene item in every scene.
#
# Controlled by both an OBS hotkey and an optional repeating
# timer.
# ------------------------------------------------------------

universal_name = "Harmony of all things"
interval       = 5
auto_align     = False
hotkey_id      = obs.OBS_INVALID_HOTKEY_ID


def capture_transform(item):
	"""Read every transform property of a scene item into a dict."""
	info = obs.obs_transform_info()
	obs.obs_sceneitem_get_info2(item, info)

	crop = obs.obs_sceneitem_crop()
	obs.obs_sceneitem_get_crop(item, crop)

	return {
		"pos_x": info.pos.x,
		"pos_y": info.pos.y,
		"rot": info.rot,
		"scale_x": info.scale.x,
		"scale_y": info.scale.y,
		"alignment": info.alignment,
		"bounds_type": info.bounds_type,
		"bounds_alignment": info.bounds_alignment,
		"bounds_x": info.bounds.x,
		"bounds_y": info.bounds.y,
		"crop_left": crop.left,
		"crop_right": crop.right,
		"crop_top": crop.top,
		"crop_bottom": crop.bottom,
	}


def apply_transform(item, t):
	"""Write a captured transform dict onto a scene item."""
	info = obs.obs_transform_info()
	info.pos.x = t["pos_x"]
	info.pos.y = t["pos_y"]
	info.rot = t["rot"]
	info.scale.x = t["scale_x"]
	info.scale.y = t["scale_y"]
	info.alignment = t["alignment"]
	info.bounds_type = t["bounds_type"]
	info.bounds_alignment = t["bounds_alignment"]
	info.bounds.x = t["bounds_x"]
	info.bounds.y = t["bounds_y"]
	obs.obs_sceneitem_set_info2(item, info)

	crop = obs.obs_sceneitem_crop()
	crop.left = t["crop_left"]
	crop.right = t["crop_right"]
	crop.top = t["crop_top"]
	crop.bottom = t["crop_bottom"]
	obs.obs_sceneitem_set_crop(item, crop)


def find_universal_transform():
	"""Search every scene for the universal source and return its transform."""
	transform = None

	scenes = obs.obs_frontend_get_scenes()
	if scenes is not None:
		for scene_source in scenes:
			scene = obs.obs_scene_from_source(scene_source)
			items = obs.obs_scene_enum_items(scene)
			if items is not None:
				for item in items:
					src = obs.obs_sceneitem_get_source(item)
					if src is not None and obs.obs_source_get_name(src) == universal_name:
						transform = capture_transform(item)
						break
				obs.sceneitem_list_release(items)
			if transform is not None:
				break
		obs.source_list_release(scenes)

	return transform


def align_sources():
	if universal_name == "":
		return

	transform = find_universal_transform()
	if transform is None:
		obs.script_log(obs.LOG_WARNING,
			"Source Guerrilla: universal source '" + universal_name + "' not found in any scene.")
		return

	aligned = 0
	scenes = obs.obs_frontend_get_scenes()
	if scenes is not None:
		for scene_source in scenes:
			scene = obs.obs_scene_from_source(scene_source)
			items = obs.obs_scene_enum_items(scene)
			if items is not None:
				for item in items:
					src = obs.obs_sceneitem_get_source(item)
					if src is None:
						continue
					if obs.obs_source_get_name(src) == universal_name:
						continue
					apply_transform(item, transform)
					aligned += 1
				obs.sceneitem_list_release(items)
		obs.source_list_release(scenes)

	obs.script_log(obs.LOG_INFO,
		"Source Guerrilla: aligned " + str(aligned) + " source(s) to '" + universal_name + "'.")


def align_pressed(props, prop):
	align_sources()


def on_hotkey(pressed):
	if pressed:
		align_sources()


# ------------------------------------------------------------
# OBS script API
# ------------------------------------------------------------

def script_description():
	return ("<b>Source Guerrilla</b><br><br>"
		"Aligns every source across all scenes to a single Universal Source. "
		"Position, scale, rotation, alignment, bounding box and crop are all copied "
		"from the universal source onto every other scene item.<br><br>"
		"Trigger it with the configured hotkey or enable automatic alignment on a timer.")


def script_defaults(settings):
	obs.obs_data_set_default_string(settings, "universal_name", "Harmony of all things")
	obs.obs_data_set_default_int(settings, "interval", 5)
	obs.obs_data_set_default_bool(settings, "auto_align", False)


def script_update(settings):
	global universal_name
	global interval
	global auto_align

	universal_name = obs.obs_data_get_string(settings, "universal_name")
	interval       = obs.obs_data_get_int(settings, "interval")
	auto_align     = obs.obs_data_get_bool(settings, "auto_align")

	obs.timer_remove(align_sources)
	if auto_align and universal_name != "":
		obs.timer_add(align_sources, interval * 1000)


def script_properties():
	props = obs.obs_properties_create()

	p = obs.obs_properties_add_list(props, "universal_name", "Universal Source",
		obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING)
	sources = obs.obs_enum_sources()
	if sources is not None:
		for source in sources:
			name = obs.obs_source_get_name(source)
			obs.obs_property_list_add_string(p, name, name)
		obs.source_list_release(sources)

	obs.obs_properties_add_bool(props, "auto_align", "Automatically align on a timer")
	obs.obs_properties_add_int(props, "interval", "Alignment Interval (seconds)", 1, 3600, 1)
	obs.obs_properties_add_button(props, "align_button", "Align Now", align_pressed)

	return props


def script_load(settings):
	global hotkey_id

	hotkey_id = obs.obs_hotkey_register_frontend(
		"source_guerrilla.align", "Source Guerrilla: Align to Universal Source", on_hotkey)
	hotkey_save_array = obs.obs_data_get_array(settings, "source_guerrilla.align")
	obs.obs_hotkey_load(hotkey_id, hotkey_save_array)
	obs.obs_data_array_release(hotkey_save_array)


def script_save(settings):
	hotkey_save_array = obs.obs_hotkey_save(hotkey_id)
	obs.obs_data_set_array(settings, "source_guerrilla.align", hotkey_save_array)
	obs.obs_data_array_release(hotkey_save_array)


def script_unload():
	obs.timer_remove(align_sources)
