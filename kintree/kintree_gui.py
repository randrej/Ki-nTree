#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
# Webbrowser
import webbrowser

# Settings
import config.settings as settings
# PySimpleGUI
import PySimpleGUI as sg
# Digi-Key API
import search.digikey_api as digikey_api
# SnapEDA API
import search.snapeda_api as snapeda_api
# Progress
from common import progress
# Tools
from common.tools import cprint, create_library
# Interface
from config import config_interface
# InvenTree
from database import inventree_interface
# FuzzyWuzzy
from fuzzywuzzy import fuzz
# KiCad
from kicad import kicad_interface


def search_api_settings_window():
	''' Part search API settings window '''
	user_settings = config_interface.load_file(settings.CONFIG_DIGIKEY_API)

	search_api_layout = [
		[
			sg.Text('Enter Digi-Key API Client ID:'),
			sg.InputText(user_settings['DIGIKEY_CLIENT_ID'], key='client_id'),			
		],
		[
			sg.Text('Enter Digi-Key API Client Secret:'),
			sg.InputText(user_settings['DIGIKEY_CLIENT_SECRET'], key='client_secret'),			
		],
		[ 
			sg.Button('Test',size=(15,1)),
			sg.Button('Save',size=(15,1)),
		],
	]
	search_api_window = sg.Window(
		'Digi-Key API (v3) Settings', search_api_layout, location=(500, 500)
	)

	while True:
		api_event, api_values = search_api_window.read()

		def save_settings(user_settings: dict):
			new_settings = {
				'DIGIKEY_CLIENT_ID': api_values['client_id'],
				'DIGIKEY_CLIENT_SECRET': api_values['client_secret'],
			}
			user_settings = {**user_settings, **new_settings}
			config_interface.dump_file(user_settings, settings.CONFIG_DIGIKEY_API)

		if api_event == sg.WIN_CLOSED:
			search_api_window.close()
			return
		elif api_event == 'Test':
			# Automatically save settings
			save_settings(user_settings)
			if digikey_api.test_digikey_api_connect():
				result_message = f'Sucessfully connected to Digi-Key API'
			else:
				result_message = f'Failed to connect to Digi-Key API'
			sg.popup_ok(result_message,
						title='Digi-Key API Connect Test',
						location=(500, 500))
		else:
			save_settings(user_settings)
			search_api_window.close()
			return

def inventree_settings_window():
	''' InvenTree settings window '''

	user_settings = config_interface.load_inventree_user_settings(settings.CONFIG_INVENTREE)

	inventree_layout = [
		[
			sg.Text('Enter InvenTree Address:'),
			sg.InputText(user_settings['SERVER_ADDRESS'], key='server'),			
		],
		[
			sg.Text('Enter Username:'),
			sg.InputText(user_settings['USERNAME'], key='username'),			
		],
		[
			sg.Text('Enter Password:'),
			sg.InputText(user_settings['PASSWORD'], key='password', password_char='*'),			
		],
		[ 
			sg.Button('Test',size=(15,1)),
			sg.Button('Save',size=(15,1)),
		],
	]
	inventree_window = sg.Window(
		'InvenTree Settings', inventree_layout, location=(500, 500)
	)

	while True:
		inv_event, inv_values = inventree_window.read()

		def save_settings():
			config_interface.save_inventree_user_settings(enable=settings.ENABLE_INVENTREE,
														  server=inv_values['server'],
														  username=inv_values['username'],
														  password=inv_values['password'],
														  user_config_path=settings.CONFIG_INVENTREE)

		if inv_event == sg.WIN_CLOSED:
			inventree_window.close()
			return
		elif inv_event == 'Test':
			# Automatically save settings
			save_settings()
			if inventree_interface.connect_to_server():
				result_message = f'Sucessfully connected to InvenTree server'
			else:
				result_message = f'Failed to connect to InvenTree server'
			sg.popup_ok(result_message,
						title='InvenTree Connect Test',
						location=(500, 500))
		else:
			save_settings()
			inventree_window.close()
			return

def kicad_settings_window():
	''' KiCad settings window '''
	kicad_user_settings = config_interface.load_file(settings.CONFIG_KICAD)
	KICAD_SYMBOLS_PATH = kicad_user_settings['KICAD_SYMBOLS_PATH']
	KICAD_TEMPLATES_PATH = kicad_user_settings['KICAD_TEMPLATES_PATH']
	KICAD_FOOTPRINTS_PATH = kicad_user_settings['KICAD_FOOTPRINTS_PATH']

	kicad_layout = [
		[
			sg.Text('Select Symbol Libraries Folder:'),
			sg.InputText(KICAD_SYMBOLS_PATH, key='library'),
			sg.FolderBrowse(target='library', initial_folder=KICAD_SYMBOLS_PATH),
		],
		[
			sg.Text('Select Symbol Templates Folder:'),
			sg.InputText(KICAD_TEMPLATES_PATH, key='template'),
			sg.FolderBrowse(target='template', initial_folder=KICAD_TEMPLATES_PATH),
		],
		[
			sg.Text('Select Footprint Libraries Folder:'),
			sg.InputText(KICAD_FOOTPRINTS_PATH, key='footprint'),
			sg.FolderBrowse(target='footprint', initial_folder=KICAD_FOOTPRINTS_PATH),
		],
		[ sg.Button('Save',size=(10,1)), ],
	]
	kicad_window = sg.Window(
		'KiCad Settings', kicad_layout, location=(500, 500)
	)
	kcd_event, kcd_values = kicad_window.read()
	if kcd_event == sg.WIN_CLOSED:  # if user closes window
		pass
	else:
		new_settings = {	
					'KICAD_SYMBOLS_PATH': kcd_values['library'],
					'KICAD_TEMPLATES_PATH': kcd_values['template'],
					'KICAD_FOOTPRINTS_PATH': kcd_values['footprint'], 
				}
		for name, path in new_settings.items():
			if path == '':
				cprint(f'[INFO]\tWarning: KiCad {name} path is empty', silent=settings.SILENT)
			# Check if path has trailing slash
			elif path[-1] != os.sep:
				new_settings[name] = path + os.sep
		# Read user settings file
		kicad_user_settings = {**kicad_user_settings, **new_settings}
		# Write to user settings file
		config_interface.dump_file(kicad_user_settings, settings.CONFIG_KICAD)
		
	kicad_window.close()
	return

def snapeda_window(part_number: str):
	''' Display SnapEDA API results '''

	# TODO: loading animation
	# loading_img = os.path.join(settings.PROJECT_DIR, 'images', 'loading.gif')
	
	snapeda_layout = [
		[sg.Text('Downloading SnapEDA information...')],
	]

	snapeda_window = sg.Window(
		'SnapEDA', snapeda_layout, location=(500, 500)
	)

	while True:
		snapeda_event, snapeda_values = snapeda_window.read(timeout=10)

		response = snapeda_api.fetch_snapeda_part_info(part_number)
		data = snapeda_api.parse_snapeda_response(response)
		images = snapeda_api.download_snapeda_images(data)

		break

	snapeda_window.close()

	snapeda_layout = []

	if data['has_single_result']:
		# Check if symbol and footprint available for download on SnapEDA's website
		if data['has_symbol'] and data['has_footprint']:
			snapeda_msg = f'Symbol and Footprint are available on SnapEDA!\t'
			snapeda_layout.append([sg.Text(snapeda_msg), sg.Button('Download')])

			# Display images
			if not None in images.values():
				snapeda_layout.append([sg.Image(images['symbol']), sg.Image(images['footprint'])])
			else:
				if images['symbol']:
					snapeda_layout.append([sg.Image(images['symbol'])])
					
				if images['footprint']:
					snapeda_layout.append([sg.Image(images['footprint'])])
				else:
					if not images['symbol']:
						snapeda_layout.append([sg.Text('(No preview available)')])
		elif data['has_symbol']:
			snapeda_msg = f'Symbol is available on SnapEDA!\t'
			snapeda_layout.append([sg.Text(snapeda_msg), sg.Button('Download')])

			# Display images
			if images['symbol']:
				snapeda_layout.append([sg.Image(images['symbol'])])
			else:
				snapeda_layout.append([sg.Text('(No preview available)')])
		elif data['has_footprint']:
			snapeda_msg = f'Footprint is available on SnapEDA!\t'
			snapeda_layout.append([sg.Text(snapeda_msg), sg.Button('Download')])

			# Display images
			if images['footprint']:
				snapeda_layout.append([sg.Image(images['footprint'])])
			else:
				snapeda_layout.append([sg.Text('(No preview available)')])
		else:
			pass
	else:
		if data['part_url']:
			snapeda_msg = f'Multiple part matches on SnapEDA\t'
			snapeda_layout.append([sg.Text(snapeda_msg), sg.Button('See Results')])

	if not snapeda_layout:
		snapeda_msg = 'Unfortunately, symbol and footprint were not found on SnapEDA :('
		snapeda_layout.append([sg.Text(snapeda_msg)])

	snapeda_window = sg.Window(
		'SnapEDA', snapeda_layout, location=(500, 500)
	)

	while True:
		snapeda_event, snapeda_values = snapeda_window.read()

		if snapeda_event == sg.WIN_CLOSED:  # if user closes window
			break
		elif snapeda_event == 'Download' or snapeda_event == 'See Results':
			try:
				webbrowser.open(data['part_url'], new=2)
			except TypeError:
				cprint(f'[INFO]\tError: Failed to open URL', silent=settings.SILENT)
		else:
			pass
		
	snapeda_window.close()

def add_custom_part(part_data: dict) -> dict:
	''' Add custom part (bypass Digi-Key search) '''
	user_values = {}
	add_custom_layout = []

	def get_default(part_data, key):
		try:
			default_key = list(part_data[key].keys())[0]
			default_value = part_data[key][default_key][0]
		except:
			default_key = ''
			default_value = ''

		return default_key, default_value

	skip_items = ['category', 'IPN', 'image', 'inventree_url', 'parameters']
	input_keys = []
	for key, value in settings.inventree_part_template.items():
		if key in skip_items:
			pass
		elif key == 'supplier' or key == 'manufacturer':
			# Get default values
			name_default, number_default = get_default(part_data, key)

			sub_key = key + '_name'
			add_custom_layout.append([
										sg.Text(sub_key.replace('_', ' ').title(), size=(22, 1)),
										sg.InputText(name_default, size=(38, 1), key=sub_key),
									])
			input_keys.append(sub_key)

			sub_key = key + '_part_number'
			add_custom_layout.append([
										sg.Text(sub_key.replace('_', ' ').title(), size=(22, 1)),
										sg.InputText(number_default, size=(38, 1), key=sub_key),
									])
			input_keys.append(sub_key)
		else:
			default = part_data.get(key, '')
			if not default:
				default = ''

			add_custom_layout.append([
										sg.Text(key.capitalize(), size=(22, 1)),
										sg.InputText(default, size=(38, 1), key=key),
									])
			input_keys.append(key)

	if part_data:
		add_custom_layout.append([ sg.Button('Submit', size=(25,1)), ])
		window_title = 'Update Part Data'
	else:
		add_custom_layout.append([ sg.Button('CREATE', size=(59,1)), ])
		window_title = 'Add Custom Part'

	add_custom_window = sg.Window(
		window_title, add_custom_layout, location=(500, 500)
	)

	while True:
		cstm_event, cstm_values = add_custom_window.read()

		if cstm_event == sg.WIN_CLOSED:  # if user closes window
			return None
		else:
			for key in input_keys:
				user_values[key] = cstm_values[key]

			if not cstm_values['name'] and not cstm_values['description']:
				sg.popup_ok(f'Missing "Name" and "Description"',
							title='Error',
							location=(500, 500))
			elif not cstm_values['name']:
				sg.popup_ok(f'Missing "Name"',
							title='Error',
							location=(500, 500))
			elif not cstm_values['description']:
				sg.popup_ok(f'Missing "Description"',
							title='Error',
							location=(500, 500))
			else:
				break
		
	add_custom_window.close()
	return user_values

def user_defined_categories(category=None, subcategory=None, extend=False) -> list:
	''' User defined categories window '''
	categories = [None, None]

	if extend:
		# Load and synchronize supplier categories with InvenTree categories
		categories_dict = config_interface.sync_inventree_supplier_categories(inventree_config_path=settings.CONFIG_CATEGORIES,
																			  supplier_config_path=settings.CONFIG_DIGIKEY_CATEGORIES)
	else:
		# Load categories from supplier configuration
		categories_dict = config_interface.load_supplier_categories(supplier_config_path=settings.CONFIG_DIGIKEY_CATEGORIES,
																	clean=True)

	# Category choices
	categories_choices = []
	subcategories_choices = []
	subcategory_default = None

	try:
		for cat in categories_dict.keys():
			categories_choices.append(cat)

			if category:
				if category == cat:
					# Subcategory choices
					for subcat in categories_dict[cat].keys():
						if subcat not in subcategories_choices:
							subcategories_choices.append(subcat)

		if subcategory:
				subcategory_default = subcategory
	except:
		# categories_dict is None
		pass

	# Set default list for subcategory choices
	if not subcategories_choices:
		if not subcategory_default:
			subcategories_choices = ['None']
		else:
			subcategories_choices = [subcategory_default]
	if not subcategory_default:
		subcategory_default = subcategories_choices[0]

	category_layout = [
		[
			sg.Text('Select Category:'),
			sg.Combo(sorted(categories_choices), default_value=category, key='category'),
			sg.Button('Confirm'),
		],
		[
			sg.Text('Select Subcategory:'),
			sg.Combo(sorted(subcategories_choices), default_value=subcategory_default, size=(20,1), key='subcategory_sel'),
			sg.Text('Or Enter Name:'),
			sg.In(size=(20,1),key='subcategory_man'),
		],
		[
			sg.Button('Submit'),
		],
	]

	category_window = sg.Window('Categories', category_layout, location=(500, 500))
	category_event, category_values = category_window.read()
	category_window.close()

	if category_event == sg.WIN_CLOSED:
		return categories
	elif category_event == 'Confirm':
		return user_defined_categories(category_values['category'], extend=settings.ENABLE_INVENTREE)
	else:
		categories[0] = category_values['category']
		if category_values['subcategory_man']:
			categories[1] = category_values['subcategory_man']
		else:
			categories[1] = category_values['subcategory_sel']
		
		if '' in categories:
			missing_category = 'Missing category information'
			cprint(f'[INFO]\tError: {missing_category}')
			sg.popup_ok(missing_category,
						title='Categories',
						location=(500, 500))

		return categories

def user_defined_symbol_template_footprint(categories: list,
										   part_number: str,
										   symbol_lib=None,
										   template=None,
										   footprint_lib=None,
										   footprint=None,
										   symbol_confirm=False,
										   footprint_confirm=False):
	''' Symbol and Footprint user defined window '''
	symbol = None

	if symbol_confirm and '---' not in symbol_lib:
		if not config_interface.add_library_path(user_config_path=settings.CONFIG_KICAD_CATEGORY_MAP,
												 category=categories[0],
												 symbol_library=symbol_lib):
			cprint(f'[INFO]\tWarning: Failed to add symbol library to {categories[0]} category', silent=settings.SILENT)

	if footprint_confirm and '---' not in footprint_lib:
		if not config_interface.add_footprint_library(user_config_path=settings.CONFIG_KICAD_CATEGORY_MAP,
													  category=categories[0],
													  library_folder=footprint_lib):
			cprint(f'[INFO]\tWarning: Failed to add footprint library to {categories[0]} category', silent=settings.SILENT)
	
	# Load user settings
	settings.load_kicad_settings()

	def fuzzy_default(value:str, choices:list) -> str:
		match = None
		LIMIT = 85

		for item in choices:
			fuzzy_match = fuzz.partial_ratio(value, item)
			display_result = f'"{value}" ?= "{item}"'.ljust(50)
			cprint(f'{display_result} => {fuzzy_match}', silent=settings.HIDE_DEBUG)
			if fuzzy_match >= LIMIT:
				match = item
				break

		return match

	def build_choices(items: dict, category: str, subcategory=None) -> list:
		choices = []

		try:
			for key, value in items[category].items():
				if value:
					choices.append(key)
		except:
			if subcategory:
				error_message = f'Warning: No templates defined for "{category}"'
				cprint(f'[INFO]\t{error_message}', silent=settings.SILENT)
				# sg.popup_ok(error_message, title='No Templates', location=(500, 500))

		if subcategory:
			# Load templates only for given category/subcategory pair
			return sorted(choices)

		# Separate libraries not officially assigned to category
		if choices:
			choices.append('-' * 10)

		more_choices = []
		for cat in items.keys():
			if cat != category and cat != 'uncategorized':
				for key in items[cat].keys():
					more_choices.append(key)

		# Process uncategorized entries
		try:
			for item in items['uncategorized']:
				more_choices.append(item)
		except:
			# error_message = f'Warning: No libraries defined for "{category}"'
			# cprint(f'[INFO]\t{error_message}', silent=settings.SILENT)
			# sg.popup_ok(error_message, title='No Libraries', location=(500, 500))
			pass
		try:
			choices.extend(sorted(more_choices))
		except:
			pass

		return choices

	# Load symbol libraries
	if not settings.KICAD_SYMBOLS_PATH:
		sg.popup_ok(f'Error: KiCad symbol library folder path is not defined ("Settings > KiCad")',
					title='KiCad Symbol Library Folder',
					location=(500, 500))
		return symbol, template, footprint

	symbol_library = config_interface.load_libraries_paths(user_config_path=settings.CONFIG_KICAD_CATEGORY_MAP,
														   library_path=settings.KICAD_SYMBOLS_PATH)
	# cprint(symbol_library)
	if not symbol_library:
		sg.popup_ok(f'Error: Symbol library files were not found in {settings.KICAD_SYMBOLS_PATH}',
					title='KiCad Symbol Library Folder',
					location=(500, 500))
		return symbol, template, footprint
	
	# Build symbol choices
	symbol_lib_choices = build_choices(symbol_library, categories[0])
	if symbol_lib:
		symbol_lib_default = symbol_lib
	else:
		# Try fuzzy matching
		symbol_lib_default = fuzzy_default(categories[0], symbol_lib_choices)
		
		if not symbol_lib_default:
			symbol_lib_default = symbol_lib_choices[0]

	# Load templates
	if not settings.KICAD_TEMPLATES_PATH:
		sg.popup_ok(f'Error: KiCad template folder path is not defined ("Settings > KiCad")',
					title='KiCad Template Folder',
					location=(500, 500))
		return symbol, template, footprint

	templates = config_interface.load_templates_paths(user_config_path=settings.CONFIG_KICAD_CATEGORY_MAP,
													  template_path=settings.KICAD_TEMPLATES_PATH)
	# cprint(templates)
	if not templates:
		sg.popup_ok(f'Error: Template files were not found in {settings.KICAD_TEMPLATES_PATH}',
					title='KiCad Template Folder',
					location=(500, 500))
		return symbol, template, footprint
	
	# Build template choices
	template_default = None

	if not categories[0]:
		category = symbol_lib_choices[0]
	else:
		category = categories[0]
	if not categories[1]:
		subcategory = 'None'
	else:
		subcategory = categories[1]
	try:
		template_choices = build_choices(templates, category, subcategory)
	except:
		pass

	# Select default template
	if template_choices:
		# If template was selected by user then use it
		if template:
			template_default = template
		else:
			# Automatically select template from subcategory
			template_default = subcategory if templates[category].get(subcategory, None) else None
			# If automatic match failed then select first entry
			if not template_default:
				template_default = template_choices[0]
	else:
		# No template matching
		template_choices = ['None']
		template_default = template_choices[0]

	# Load footprint libraries
	if not settings.KICAD_FOOTPRINTS_PATH:
		sg.popup_ok(f'Error: KiCad footprint library folder path is not defined ("Settings > KiCad")',
					title='KiCad Footprint Library Folder',
					location=(500, 500))
		return symbol, template, footprint

	footprint_library = config_interface.load_footprint_paths(user_config_path=settings.CONFIG_KICAD_CATEGORY_MAP,
															  footprint_path=settings.KICAD_FOOTPRINTS_PATH)
	# cprint(f'{footprint_library=}')
	if not footprint_library:
		sg.popup_ok(f'Error: Footprint library files were not found in {settings.KICAD_FOOTPRINTS_PATH}',
					title='KiCad Footprint Library Folder',
					location=(500, 500))
		return symbol, template, footprint
	
	# Build symbol choices
	footprint_lib_choices = build_choices(footprint_library, categories[0])

	# Footprint mod list
	footprint_mod_choices = []
	if footprint_lib:
		footprint_lib_default = footprint_lib
		try:
			footprint_lib_path = footprint_library[categories[0]][footprint_lib]
		except:
			pass

		try:
			footprint_mod_choices = [ item.replace('.kicad_mod','') \
									  for item in sorted(os.listdir(footprint_lib_path)) \
									  if os.path.isfile(os.path.join(footprint_lib_path, item)) ]
		except:
			cprint(f'[INFO]\tWarning: Failed fetching footprint mod files for {footprint_lib}', silent=settings.SILENT)
			# cprint(f'{footprint_lib=}\t{categories[0]}', silent=settings.HIDE_DEBUG)
			cprint(footprint_library, silent=settings.HIDE_DEBUG)
	else:
		# Try fuzzy matching
		footprint_lib_default = fuzzy_default(categories[0], footprint_lib_choices)

		if not footprint_lib_default:
			footprint_lib_default = footprint_lib_choices[0]
		try:
			footprint_lib_path = footprint_library[categories[0]][footprint_lib_default]
			footprint_mod_choices = [ item.replace('.kicad_mod','') \
									  for item in sorted(os.listdir(footprint_lib_path)) \
									  if os.path.isfile(os.path.join(footprint_lib_path, item)) ]
		except:
			cprint(f'[INFO]\tWarning: Failed fetching footprint mod files for {footprint_lib_default}', silent=settings.SILENT)
			# cprint(f'{footprint_lib_default=}\t{categories[0]}', silent=settings.HIDE_DEBUG)
			cprint(footprint_library, silent=settings.HIDE_DEBUG)

	if not footprint_mod_choices:
		footprint_mod_choices = ['None']
		footprint_mod_default = footprint_mod_choices[0]
	else:
		if footprint:
			footprint_mod_default = footprint
		else:
			footprint_mod_default = None

	library_layout = [
		[
			sg.Text('Select Symbol Library:'),
			sg.Combo(symbol_lib_choices, default_value=symbol_lib_default, key='symbol_lib'),
			sg.Button('Confirm'),
		],
		[
			sg.Text(f'Select Symbol Template ({categories[0]}):'),
			sg.Combo(template_choices, default_value=template_default, key='template'),
		],
		[
			sg.Text('Select Footprint Library:'),
			sg.Combo(footprint_lib_choices, default_value=footprint_lib_default, key='footprint_lib'),
			sg.Button('Confirm'),
		],
		[
			sg.Text('Select Footprint:'),
			sg.Combo(footprint_mod_choices, default_value=footprint_mod_default, key='footprint_mod_sel'),
			sg.Text('Or Enter Name:'),
			sg.In(size=(20,1),key='footprint_mod_man'),
		],
		[ sg.Text('') ],
	]

	if part_number:
		library_layout.append([ sg.Button('Check SnapEDA'), sg.Button('Submit') ])
	else:
		library_layout.append([ sg.Button('Submit') ])

	library_window = sg.Window('KiCad Libraries', library_layout, location=(500, 500))
	lib_event, lib_values = library_window.read()
	library_window.close()

	if lib_event == sg.WIN_CLOSED:
		return None, None, None
	elif lib_event == 'Check SnapEDA':
		# SnapEDA window
		snapeda_window(part_number)
		return user_defined_symbol_template_footprint(categories=categories,
													  part_number=part_number,
													  symbol_lib=lib_values['symbol_lib'],
													  template=lib_values['template'],
													  footprint_lib=lib_values['footprint_lib'],
													  footprint=lib_values['footprint_mod_sel'])
	# Symbol library confirmation
	elif lib_event == 'Confirm':
		return user_defined_symbol_template_footprint(categories=categories,
													  part_number=part_number,
													  symbol_lib=lib_values['symbol_lib'],
													  template=lib_values['template'],
													  footprint_lib=lib_values['footprint_lib'],
													  footprint=lib_values['footprint_mod_sel'],
													  symbol_confirm=True)
	# Footprint library confirmation
	elif lib_event == 'Confirm0':
		return user_defined_symbol_template_footprint(categories=categories,
													  part_number=part_number,
													  symbol_lib=lib_values['symbol_lib'],
													  template=lib_values['template'],
													  footprint_lib=lib_values['footprint_lib'],
													  footprint=None,
													  footprint_confirm=True)
	else:
		symbol = lib_values['symbol_lib']
		template = lib_values['template']
		if lib_values['footprint_mod_man']:
			footprint = lib_values['footprint_lib'] + ':' + lib_values['footprint_mod_man']
		elif lib_values['footprint_mod_sel'] and lib_values['footprint_mod_sel'] != 'None':
			footprint = lib_values['footprint_lib'] + ':' + lib_values['footprint_mod_sel']
		
		if not footprint:
			footprint = lib_values['footprint_lib'] + ':' + settings.footprint_name_default

		# Save paths
		if not config_interface.add_library_path(user_config_path=settings.CONFIG_KICAD_CATEGORY_MAP,
												 category=categories[0],
												 symbol_library=lib_values['symbol_lib']):
			cprint(f'[INFO]\tWarning: Failed to add symbol library to {categories[0]} category', silent=settings.SILENT)

		if not config_interface.add_footprint_library(user_config_path=settings.CONFIG_KICAD_CATEGORY_MAP,
													  category=categories[0],
													  library_folder=lib_values['footprint_lib']):
			cprint(f'[INFO]\tWarning: Failed to add footprint library to {categories[0]} category', silent=settings.SILENT)

		return symbol, template, footprint

# Main
def main():
	''' Main GUI window '''

	# Create user configuration files
	if not settings.create_user_config_files():
		cprint('\n[ERROR]\tSome Ki-nTree configuration files seem to be missing')
		return

	CREATE_CUSTOM = False

	# Select PySimpleGUI theme
	# sg.theme_previewer() # Show all
	sg.theme('DarkTeal10')

	# Main Menu
	menu_def = [
		['Settings', 
			[	
				'Digi-Key',
				'KiCad',
				'InvenTree',
			],
		],
		[ 'More', 
			[
				# 'Synchronize',
				'Custom Part',
			],
		],
	]
	# Main Window
	layout = [
		[sg.Menu(menu_def,)],
		[
			sg.Text('Enter Part Number:'),
			sg.InputText(key='part_number'),
		],
		[
			sg.Checkbox('Add to KiCad', enable_events=True, default=settings.ENABLE_KICAD, key='enable_kicad'),
			sg.Checkbox('Add to InvenTree', enable_events=True, default=settings.ENABLE_INVENTREE, key='enable_inventree'),
		],
		[
			sg.Button('CREATE', size=(59,1)),
		],
	]

	# Create the Window
	window = sg.Window(f'Ki-nTree [{settings.version}]', 
						layout, 
						location=(500, 500) )

	# Event Loop to process 'events' and get the 'values' of the inputs
	while True:
		if CREATE_CUSTOM:
			event = 'CREATE_CUSTOM'
		else:
			event, values = window.read()

		if event == sg.WIN_CLOSED:  # if user closes window or clicks cancel
			break

		if event == 'Digi-Key':
			search_api_settings_window()
		elif event == 'InvenTree':
			inventree_settings_window()
		elif event == 'KiCad':
			kicad_settings_window()
		elif 'enable' in event:
			settings.set_inventree_enable_flag(values['enable_inventree'], save=True)
			settings.set_kicad_enable_flag(values['enable_kicad'], save=True)
		elif event == 'Custom Part':
			CREATE_CUSTOM = True
		else:
			# Adding part information to InvenTree
			categories = [None, None]
			symbol = None
			template = None
			footprint = None
			new_part = False
			part_pk = 0
			part_info = {}
			part_data = {}
			progressbar = False
			actions_complete = False

			# Check either KiCad or InvenTree are enabled
			if not settings.ENABLE_KICAD and not settings.ENABLE_INVENTREE:
				inventree_connect = False
				sg.popup_ok(f'Please select an endpoint (KiCad and/or InvenTree)',
							title='No endpoint selected',
							location=(500, 500))
			# Check InvenTree, if enabled
			elif settings.ENABLE_INVENTREE:
				cprint('\n[MAIN]\tConnecting to Inventree server', silent=settings.SILENT)
				inventree_connect = inventree_interface.connect_to_server()
				if not inventree_connect:
					sg.popup_ok(f'Failed to access InvenTree server\nMake sure your username and password are correct',
								title='InvenTree Server Error',
								location=(500, 500))
			elif settings.ENABLE_KICAD:
				inventree_connect = True

			# Get part information
			if inventree_connect:
				if CREATE_CUSTOM:
					custom_part_info = add_custom_part(part_data={})
					try:
						if custom_part_info['name'] and custom_part_info['description']:
							part_info = custom_part_info
							cprint('\n[MAIN]\tCustom Part', silent=settings.SILENT)
					except TypeError:
						pass
				else:
					if values['part_number']:
						# New part separation
						new_search = '-' * 20
						cprint(f'\n{new_search}', silent=settings.SILENT)

						# Load KiCad settings
						settings.load_kicad_settings()

						# Load InvenTree settings
						settings.load_inventree_settings()

						# Digi-Key Search
						part_info = inventree_interface.digikey_search(values['part_number'])

					if not part_info:
						# Missing Part Information
						sg.popup_ok(f'Failed to fetch part information...\n\n'
									'Make sure:'
									'\n- Part number is valid and not blank'
									'\n- Digi-Key API settings are correct ("Settings > Digi-Key")',
									title='Digi-Key API Search',
									location=(500, 500))

			# Get user categories
			if part_info and (settings.ENABLE_INVENTREE or settings.ENABLE_KICAD):
				if settings.ENABLE_INVENTREE:
					cprint('\n[MAIN]\tCreating part in Inventree', silent=settings.SILENT)

				categories = inventree_interface.get_categories(part_info=part_info,
																supplier_only=False)
			
				# If categories do not exist: request user to fill in categories
				if not categories[0]:
					categories = user_defined_categories(extend=settings.ENABLE_INVENTREE)
					if categories[0]:
						cprint(f'[INFO]\tCategory: "{categories[0]}"', silent=settings.SILENT)
					if categories[1]:
						cprint(f'[INFO]\tSubcategory: "{categories[1]}"', silent=settings.SILENT)
				elif categories[0] and not categories[1]:
					categories = user_defined_categories(category=categories[0],
														 extend=settings.ENABLE_INVENTREE)
					if categories[1]:
						cprint(f'[INFO]\tUpdated Category: "{categories[0]}"', silent=settings.SILENT)
						cprint(f'[INFO]\tSubcategory: "{categories[1]}"', silent=settings.SILENT)
				else:
					# Ask user to re-confirm categories (pre-filled)
					categories = user_defined_categories(category=categories[0], 
														 subcategory=categories[1],
														 extend=settings.ENABLE_INVENTREE)
					cprint(f'[INFO]\tUser Category: "{categories[0]}"', silent=settings.SILENT)
					cprint(f'[INFO]\tUser Subcategory: "{categories[1]}"', silent=settings.SILENT)

			# Get user part info
			if not (categories[0] and categories[1]):
				part_info = {}
			else:
				if CREATE_CUSTOM:
					# Translate custom part data
					part_info = inventree_interface.translate_form_to_digikey(part_info=part_info,
																			  categories=categories,
																			  custom=True)
				else:
					# Add to supplier categories configuration file
					category_dict = {
						categories[0]:
							{ categories[1]: part_info['subcategory'] }
					}
					if not config_interface.add_supplier_category(category_dict, settings.CONFIG_DIGIKEY_CATEGORIES):
						config_file = settings.CONFIG_DIGIKEY_CATEGORIES.split(os.sep)[-1]
						cprint(f'[INFO]\tWarning: Failed to add new supplier category to {config_file} file', silent=settings.SILENT)
						cprint(f'[DBUG]\tcategory_dict = {category_dict}', silent=settings.SILENT)

					# Confirm part data with user
					form_data = add_custom_part(inventree_interface.translate_digikey_to_inventree(part_info=part_info,
																								   categories=categories,
																								   skip_params=True))
					if form_data:
						# Translate to part info format
						user_part_info = inventree_interface.translate_form_to_digikey(part_info=form_data,
																				  	   categories=categories,
																				  	   custom=False)

						# Merge original part_info with user_part_info
						part_info = {**part_info, **user_part_info}
					else:
						# User did not proceed
						part_info = {}

			# Set KiCad user libraries and symbol/footprint
			if part_info and settings.ENABLE_KICAD:
				
				# Request user to select symbol and footprint libraries
				symbol, template, footprint = user_defined_symbol_template_footprint(categories, part_info['manufacturer_part_number'])
				# cprint(f'{symbol=}\t{template=}\t{footprint=}', silent=settings.HIDE_DEBUG)
				if not symbol and not footprint:
					part_info = {}
			
			if part_info:
				# All user actions were completed
				actions_complete = True

				# Create progress bar window
				progressbar = progress.create_progress_bar_window()

				# InvenTree
				if (symbol and footprint) or settings.ENABLE_INVENTREE:
					
					# Create part in InvenTree
					if settings.ENABLE_INVENTREE:
						new_part, part_pk, part_data = inventree_interface.inventree_create(part_info=part_info,
																							categories=categories,
																							kicad=settings.ENABLE_KICAD,
																							symbol=symbol,
																							footprint=footprint,
																							show_progress=progressbar,
																							is_custom=CREATE_CUSTOM)
						if not part_data:
							cprint(f'[INFO]\tError: Could not add part to InvenTree', silent=settings.SILENT)

					else:
						if not categories[0]:
							pseudo_categories = [symbol, None]
							part_data = inventree_interface.translate_digikey_to_inventree(part_info=part_info,
																						   categories=pseudo_categories)
						else:
							part_data = inventree_interface.translate_digikey_to_inventree(part_info=part_info,
																						   categories=categories)
							part_data['parameters']['Symbol'] = symbol
							part_data['parameters']['Footprint'] = footprint
						if not part_data:
							cprint(f'[INFO]\tError: Could not format part data', silent=settings.SILENT)

			if part_data:
				if not settings.ENABLE_INVENTREE:
					# Replace IPN with part name if InvenTree is not used (no part number)
					if CREATE_CUSTOM:
						try:
							manufacturer = part_data['manufacturer'].keys()[0]
							part_data['IPN'] = part_data['manufacturer'][manufacturer][0]
						except:
							part_data['IPN'] = part_data['name']
					else:
						part_data['IPN'] = values['part_number']
					if part_data['datasheet']:
						part_data['inventree_url'] = part_data['datasheet']

				# KiCad
				# Initialize success flag
				kicad_success = False

				if settings.ENABLE_KICAD:
					# Reload paths
					settings.load_kicad_settings()
					symbol_libraries_paths = config_interface.load_libraries_paths(settings.CONFIG_KICAD_CATEGORY_MAP, settings.KICAD_SYMBOLS_PATH)
					symbol_templates_paths = config_interface.load_templates_paths(settings.CONFIG_KICAD_CATEGORY_MAP, settings.KICAD_TEMPLATES_PATH)

					# Adding part symbol to KiCAD
					cprint(f'\n[MAIN]\tAdding part to KiCad', silent=settings.SILENT)

					if not symbol:
						kicad_error = 'Incorrect symbol choice'
						cprint(f'[INFO]\tError: {kicad_error}', silent=settings.SILENT)
					elif not template:
						kicad_error = 'Incorrect template choice'
						cprint(f'[INFO]\tError: {kicad_error}', silent=settings.SILENT)
					elif not footprint:
						kicad_error = 'Incorrect footprint choice'
						cprint(f'[INFO]\tError: {kicad_error}', silent=settings.SILENT)
					else:
						try:
							library_path = symbol_libraries_paths[categories[0]][symbol]
						except:
							library_path = symbol_libraries_paths[symbol][symbol]
							
						if template == 'None':
							cprint(f'[INFO]\tWarning: Missing template, using default', silent=settings.SILENT)
							template_path = settings.KICAD_TEMPLATES_PATH + 'default.lib'
						else:
							try:
								template_path = symbol_templates_paths[categories[0]][template]
							except:
								template_path = symbol_templates_paths[symbol][template]

						try:
							library_directory = os.path.dirname(library_path)
						except:
							library_directory = None
							cprint(f'[INFO]\tError: Failed to map library file', silent=settings.SILENT)
						
						if library_directory:
							if settings.AUTO_GENERATE_LIB:
								create_library(library_directory, symbol, settings.symbol_template_lib)

							try:
								kicad_success, kicad_new_part = kicad_interface.inventree_to_kicad(part_data=part_data,
																								   library_path=library_path,
																								   template_path=template_path,
																								   show_progress=progressbar)
							except:
								cprint(f'[INFO]\tError: Failed to add part to KiCad (incomplete InvenTree data)', silent=settings.SILENT)

			# Final result message
			result_message = ''

			if actions_complete:
				# Result pop-up window
				if settings.ENABLE_INVENTREE:
					if not new_part and part_pk:
						result_message = 'Part already in InvenTree database'
					elif not new_part and not part_pk:
						result_message = 'Error while adding part to InvenTree (check output)'
						# Indicate if part categories are incorrect
						if not categories[0] or categories[1]:
							result_message += '\n\nPart categories were not set properly or do not exist on InvenTree'
					elif not part_data:
						result_message = 'Part data not found - Check part number'
					else:
						result_message = 'Part added to InvenTree database'

				if settings.ENABLE_INVENTREE and settings.ENABLE_KICAD:
					result_message += '\n'

				if settings.ENABLE_KICAD:
					if not kicad_success:
						result_message += 'Error while adding part in KiCad (check output)'
						try:
							result_message += f'\nINFO: {kicad_error}'
						except:
							pass
					else:
						if kicad_new_part:
							result_message += 'Part added to KiCad library'
						else:
							result_message += 'Part already in KiCad library'

			# Update progress bar to complete and close window
			if progressbar:
				progress.update_progress_bar_window(progress.MAX_PROGRESS)
				progress.close_progress_bar_window()

			if result_message:
				sg.popup_ok(result_message, title='Results', location=(500, 500))

			if part_data.get('inventree_url', None):
				# Auto-Open Browser Window
				cprint(f'\n[MAIN]\tOpening URL {part_data["inventree_url"]} in browser',
					   silent=settings.SILENT)
				try:
					webbrowser.open(part_data['inventree_url'], new=2)
				except TypeError:
					cprint(f'[INFO]\tError: Failed to open URL', silent=settings.SILENT)

			# Reset create custom flag
			CREATE_CUSTOM = False

	window.close()

if __name__ == '__main__':
	# Disable Digi-Key API logger
	digikey_api.disable_digikey_api_logger()
	# Run main window
	main()
