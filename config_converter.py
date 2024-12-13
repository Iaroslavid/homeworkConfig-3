import argparse
import re
import sys
import yaml

def remove_comments(input_text):
    """Удаляет однострочные и многострочные комментарии."""
    input_text = re.sub(r"\*.*(?:\n|\r|$)", "", input_text)  # Удаление однострочных комментариев
    input_text = re.sub(r"/\+.*?\+/s", "", input_text, flags=re.DOTALL)  # Удаление многострочных комментариев
    return input_text.strip()


def parse_config(input_text):
    """Парсит входной текст на константы, секции и словари."""
    constants = {}
    sections = []
    dictionaries = []

    constant_pattern = r"set\s+(\w+)\s*=\s*(.*?);"
    section_pattern = r"section\s+(\w+)\s*{([^{}]*(?:{[^}]*}[^{}]*)*)}"
    dictionary_pattern = r"\[\s*(.*?)\s*\]"
    string_pattern = r'q\((.*?)\)'

    input_text = remove_comments(input_text)

    # Извлечение констант
    for match in re.finditer(constant_pattern, input_text):
        key = match.group(1)
        value = match.group(2).strip().strip('"')
        constants[key] = replace_strings(value)  # Заменяем строки

    # Извлечение секций
    for match in re.finditer(section_pattern, input_text, flags=re.DOTALL):
        section_name = match.group(1)
        section_content = match.group(2).strip()

        # Замена констант и строк внутри секции
        section_content = substitute_constants(section_content, constants)
        section_content = replace_strings(section_content)

        sections.append({
            'name': section_name,
            'content': section_content,
        })

    # Обработка словарей
    for match in re.finditer(dictionary_pattern, input_text, flags=re.DOTALL):
        dictionary_content = match.group(1)
        dictionary = parse_dictionary(dictionary_content, constants)
        dictionaries.append(dictionary)

    return constants, sections, dictionaries


def substitute_constants(content, constants):
    """Заменяет константы вида !{имя} на их значения."""
    content = re.sub(r"!{(\w+)}", lambda m: constants.get(m.group(1), f"ERROR({m.group(1)})"), content)
    return '\n'.join([line.strip() for line in content.splitlines()])  # Remove extra indentation


def replace_strings(content):
    """Заменяет строки вида q(Текст) на их эквивалент с кавычками."""
    pattern = r'q\((.*?)\)'  # Регулярное выражение для строки в формате q(Текст)
    return re.sub(pattern, lambda m: f'"{m.group(1)}"', content)  # Заменяем на строку в кавычках



def parse_dictionary(content, constants):
    """Разбирает словарь из текста."""
    pairs = content.split(',')
    dictionary = {}
    for pair in pairs:
        key_value = pair.split('=>')
        if len(key_value) == 2:
            key = key_value[0].strip()
            value = key_value[1].strip()
            value = substitute_constants(value, constants)
            value = replace_strings(value)  # Заменяем строки в значении словаря
            dictionary[key] = value
    return dictionary



def convert_to_yaml(constants, sections, dictionaries):
    """Конвертирует данные в формат YAML."""
    data = {
        'constants': constants,
        'sections': sections,
        'dictionaries': dictionaries,
    }
    return yaml.dump(data, allow_unicode=True, default_flow_style=False)

def main():
    parser = argparse.ArgumentParser(description="Конвертер конфигурационных файлов в YAML")
    parser.add_argument("output", help="Путь к выходному файлу для конфигурации")

    args = parser.parse_args()

    input_text = sys.stdin.read()

    constants, sections, dictionaries = parse_config(input_text)

    output_text = convert_to_yaml(constants, sections, dictionaries)

    try:
        with open(args.output, 'w') as outfile:
            outfile.write(output_text)
        print("Конфигурация успешно преобразована в YAML.")
    except IOError as e:
        print(f"Ошибка записи в файл: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
