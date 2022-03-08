# -*- coding: utf-8 -*-

import re
import yaml
import logging
from datetime import datetime
import os

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

dirname = os.path.dirname(__file__)

path = os.path.join(dirname, 'public/rekis_ascii_file_naming.yml')
names_yml = yaml.safe_load(open(path))


def update_season_param(resource_dict):
    for key in names_yml['seasons']:
        if re.search(key, resource_dict['cache_url'].lower()):
            resource_dict['season'] = names_yml['seasons'][key]
    if 'season' not in resource_dict:
        resource_dict['season'] = None


def format_year_with_reference_period(list_periods):
    century = datetime.today().strftime('%Y')[:2]
    cur_year_yy = datetime.today().strftime('%Y')[-2:]

    formated_years = []
    for year_combination in list_periods:
        if len(list_periods) >1:
            split_year_combination = [year_combination[i:i+2] for i in range(0, len(year_combination), 2)]   
            for year in split_year_combination:
                if year > cur_year_yy:
                    century_for_str = int(century) - 1
                else:
                    century_for_str = century
                year_yyyy = '{0}{1}'.format(century_for_str, year)
                formated_years.append(year_yyyy)
        else:
            formated_years.append(year_combination)
    
    if len(list_periods) == 2:
        cur_period = list_periods[0]
        reference_period = list_periods[1]
        cur_period_str = '{0}-{1} - vs'.format(formated_years[0], formated_years[1])
        reference_period = '{0}-{1}'.format(formated_years[2], formated_years[3])
        formated_output = [cur_period_str, reference_period]
    else:
        #start_period = str(formated_years[0])
        #end_period = str(formated_years[1])
        formated_output = formated_years

    return formated_output

def update_start_end_period_param(resource_dict):
    #Todo: make this function cleaner
    time_period = re.findall("[0-9]{4}.[0-9]{4}", resource_dict['cache_url'])
    results = ['', '']
    only_one_year = None
    if not time_period:
        if not (re.findall("[0-9]{4}", resource_dict['cache_url']) or re.findall("[0-9]{2}.[0-9]{2}", resource_dict['cache_url'])):
            if re.findall("RH_Perz", resource_dict['cache_url']):
                results = ['1961', '1990']
            elif  re.findall("KORE90", resource_dict['cache_url']) or \
                re.findall("KORE95", resource_dict['cache_url']) or \
                re.findall("KA_Auftrittshaeufigkeit", resource_dict['cache_url']):
                results = ['1991-2015 - vs', '1961-1990']
            else:
                pass
        else:
            time_with_reference_period = None
            if re.findall("[0-9]{4}vs[0-9]{4}", resource_dict['cache_url']):
                time_with_reference_period = re.findall("[0-9]{4}vs[0-9]{4}", resource_dict['cache_url'])[0]
            elif re.findall("[0-9]{2}-[0-9]{2}_zu_[0-9]{2}-[0-9]{2}", resource_dict['cache_url']):
                pattern = re.findall("[0-9]{2}-[0-9]{2}_zu_[0-9]{2}-[0-9]{2}", resource_dict['cache_url'])
                time_with_reference_period = pattern[0].replace("-", "").replace("zu", "vs").replace("_", "")
            short_formatted_time_list = re.findall("[0-9]{4}.asc", resource_dict['cache_url'])
            only_one_year = re.findall("\D_[0-9]{4}_\D", resource_dict['cache_url'])
            
            if time_with_reference_period:
                time_with_reference_period_split = re.split(r'\D+', time_with_reference_period)
                results = format_year_with_reference_period(time_with_reference_period_split)
            
            else:
                if short_formatted_time_list: 
                    if re.findall("KA_Intensi", resource_dict['cache_url']):
                        short_formatted_time = [short_formatted_time_list[0][:4], u'6190']
                        results = format_year_with_reference_period(short_formatted_time)
                    else:                
                        short_formatted_time = [short_formatted_time_list[0][:4]]
                        results = format_year_with_reference_period(short_formatted_time)
                else:
                    pass
    else:
        results = re.split(r'\D+', time_period[0])
    
    if (not only_one_year) and (len(results) == 2):
        resource_dict['start_period'], resource_dict['end_period'] = results[0], results[1]
        resource_dict['time_period_composite'] = results[0] + " - " + results[1]
    else:
        if only_one_year:
            resource_dict['time_period_composite'] = re.findall("[0-9]{4}" , only_one_year[0])[0]
        else: 
            resource_dict['time_period_composite'] = results[0]



def update_theme_param(resource_dict):
    for key in names_yml['themes']:
        # if matching state
        if re.search(key, resource_dict['cache_url']):
            for theme in names_yml['themes'][key]:
                # if matching short name
                if re.search(theme.lower(), resource_dict['cache_url'].lower()[5:]):
                    if resource_dict['season']:
                        term = u"{0} - {1}".format(resource_dict['season']['name'],
                                                  names_yml['themes'][key][theme].decode('iso-8859-15'))
                        resource_dict['theme'] = {
                            'name': term,
                            'order': resource_dict['season']['order']
                        }
                            
                    else:
                        term = names_yml['themes'][key][theme].decode('iso-8859-15')
                        resource_dict['theme'] = {
                            'name': term,
                            'order': None
                        }
                        

            if 'theme' not in resource_dict:
                resource_dict['theme'] = resource_dict['season']

def update_resources(resource_dict):
    for resource in resource_dict:
        update_season_param(resource)
        update_start_end_period_param(resource)
        update_theme_param(resource)
   
    return resource_dict

#Todo: insert function to get unique list of time periods
def set_of_time_periods(list_of_resource_dicts):
    #list_of_values = list(set((d['start_period'], d['end_period']) for d in list_of_resource_dicts))
    list_of_values = list(set((d['time_period_composite']) for d in list_of_resource_dicts))

    # following steps are for correct order of the time periods
    if len(set(len(i) for i in list_of_values)) > 1:
        x, y = list(set(len(i) for i in list_of_values))[0], list(set(len(i) for i in list_of_values))[1] 
        split_list = [sorted([i for i in list_of_values if len(i) == y]),\
                    sorted([i for i in list_of_values if len(i) == x])]
        flat_list = [item for sublist in split_list for item in sublist]
    else:
        flat_list = sorted(list_of_values)
    return flat_list

def set_of_seasons(list_of_resource_dicts):
    # list_seasons = list(set(d['season'] for d in list_of_resource_dicts))
    list_of_season_dict = list(d['season'] for d in list_of_resource_dicts)
    list_of_season_dict_without_None = [x for x in list_of_season_dict if x is not None]
    unique_list_of_season_dicts = [dict(t) for t in {tuple(d.items()) for d in list_of_season_dict_without_None}]
    sorted_unique_list_of_season_dicts = sorted(unique_list_of_season_dicts, key=lambda d: d['order']) 
    set_of_seasons = [d['name'] for d in sorted_unique_list_of_season_dicts]
    return set_of_seasons

def set_of_themes(list_of_resource_dicts):
    list_of_theme_dict = list(d['theme'] for d in list_of_resource_dicts)
    list_of_theme_dict_without_None = [x for x in list_of_theme_dict if x is not None]
    unique_list_of_themes_dicts = [dict(t) for t in {tuple(d.items()) for d in list_of_theme_dict_without_None}]
    sorted_unique_list_of_themes_dicts = sorted(unique_list_of_themes_dicts, key=lambda d: d['order']) 
    set_of_themes = [d['name'] for d in sorted_unique_list_of_themes_dicts]
    return set_of_themes