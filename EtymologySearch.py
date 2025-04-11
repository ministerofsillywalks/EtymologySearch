import requests
import lxml.etree as ET
import mwparserfromhell
import re
import functools
from langcodes import *

@functools.cache
def fetch(title):
    url = f"https://en.wiktionary.org/wiki/Special:Export/{title}"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.text

def fetch_wikitext(title):
    xml_content = fetch(title)
    root = ET.fromstring(xml_content)
    namespaces = root.nsmap
    page = root.find('page', namespaces)
    wikitext = page.find('revision/text', namespaces)
    return wikitext.text

def replace_templates(wikitext):
    wikitext_tpls = wikitext.filter_templates()
    clone_tpls = wikitext_tpls

    for tpl in wikitext_tpls:
        try:
            replace_buffer = ""
            #print(tpl)
            name =  str(tpl.name)
            #check if it is a mention template
            if name == 'm' or 'clip' in name:
                d_name = "" #no display name
                if tpl.has('2'):
                    old_word =  str(tpl.get('2').value) #mentioned word
                else:
                    old_word = ""
                replace_buffer = d_name + old_word
            
            #check if it is a root, inheritance, or derivative template
            elif 'root' in name  or 'inh' in name or 'der' in name or 'bor' in name or str(tpl.name) == 'sl':
                langcode = str(tpl.get('2').value) #langcode for the ancestor language
                d_name = Language.get(langcode).display_name()
                if tpl.has('3'):
                    old_word = " "+ str(tpl.get('3').value) #ancestor word
                else:
                    old_word = ""
                replace_buffer = d_name + old_word
            
            #check if it is a doublet template
            elif str(tpl.name) == 'doublet':
                replace_buffer += "Doublet of "
                for param in tpl.params:
                    if not str(param.name) == '1':
                        replace_buffer += str(param.value) + ", "
            
            elif str(tpl.name) == 'etymon':
                replace_buffer += "From "
                for param in tpl.params:
                    #print(param)
                    if not str(param.name) == '1':
                        replace_buffer += str(param.value) + ", "
                        if str(param.name) == 'tree':
                            break
            
            elif 'cog' in name:
                langcode = str(tpl.get('1').value) #langcode for the ancestor language
                d_name = Language.get(langcode).display_name()
                if tpl.has('2'):
                    old_word = " "+ str(tpl.get('2').value) #ancestor word
                else:
                    old_word = ""
                replace_buffer = d_name + old_word

            elif name == 'compound' or 'af' in name or 'suf' in name:
                for param in tpl.params:
                    if not str(param.name) == '1':
                        replace_buffer += str(param.value)
                        if not param == tpl.params[-1]:
                            replace_buffer += ' + '
            elif name == "multiple images":
                continue
            elif name == "glossary" or name == 'w':
                replace_buffer = str(tpl.get('1'))
            elif 'init' in name:
                replace_buffer = f"initialism of {str(tpl.get('2'))}"
            elif 'R:' in name:
                replace_buffer = ""
            else:
                replace_buffer = "TEMPLATE ERROR"

            if tpl.has('t'):
                gloss = ", "+ str(tpl.get('t').value)
            else:
                gloss = ""
            replace_buffer += gloss
            #print(replace_buffer)
            wikitext.replace(str(tpl), replace_buffer)
            output = wikitext.strip_code()
        except:
            continue
    try:
        return output
    except:
        return "No Content"

def interface():
    print("Hello! please input a word to search.")
    word = input()
    wikitext = fetch_wikitext(word)
    parsed = mwparserfromhell.parse(wikitext)
    languages = parsed.get_sections(levels=[2], flat=False)
    print(f"{len(languages)} languages found, select one:")
    for lang in range(len(languages)):
        print(str(languages[lang].get_sections(levels=[2], flat=True)[0].filter_headings()) + f" [{lang}]")
    lang_selection = int(input())
    try:
        etymologies = languages[lang_selection].get_sections(levels=[3], matches="Etymology", flat=True)
    except:
        pass
    if len(etymologies) > 0:
        print(f"{len(etymologies)} etymologies found, which one would you like to go to?")
        n = int(input())
        return replace_templates(etymologies[n])
    else:
        print("No etymologies found")
        return ''
    

while True:
    print(interface())
    print("Submit q to quit, otherwise press enter to search again")
    if input() == 'q':
        break
    else:
        continue


