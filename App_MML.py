import streamlit as st
import pandas as pd
import os

def main():
    st.title('MML Generator')

    # Сессия для хранения данных
    if 'eNB_list_data' not in st.session_state:
        st.session_state['eNB_list_data'] = []
        st.session_state['parsed_data'] = []
        st.session_state['earfcn_values'] = set()
        st.session_state['eNB_count'] = 0
        st.session_state['cell_count'] = 0

    # Загрузка файла
    uploaded_file = st.file_uploader("Загрузите список eNB", type=['txt', 'csv', 'xlsx'])

    if uploaded_file is not None:
        try:
            ext = uploaded_file.name.split('.')[-1]
            if ext == 'txt':
                data = uploaded_file.read().decode('utf-8').splitlines()
            elif ext == 'csv':
                df = pd.read_csv(uploaded_file)
                data = df.values.tolist()
            elif ext == 'xlsx':
                df = pd.read_excel(uploaded_file)
                data = df.values.tolist()
            else:
                st.error("Неподдерживаемый формат файла.")
                return
        except Exception as e:
            st.error(f"Ошибка загрузки файла: {e}")
            return

        formatted_data = []
        for line in data:
            if isinstance(line, list):
                formatted_data.append("\t".join(map(str, line)))
            else:
                formatted_data.append(line.strip())

        st.session_state['eNB_list_data'] = formatted_data
        st.session_state['parsed_data'] = parse_data(formatted_data)
        update_counts()
        update_earfcn_options()

    # Выбор типа MML
    mml_type = st.selectbox("Тип MML", ["eNB LvL MML", "Cell LvL MML"])

    # Отображение количества eNB и Cell ID
    eNB_count, cell_count = get_counts()
    st.write(f"Количество eNB: {eNB_count}")
    st.write(f"Количество Cell ID: {cell_count}")

    # Выбор EARFCN
    selected_earfcn = st.selectbox(
        "Выберите DL EARFCN",
        ["All cells"] + sorted(map(str, st.session_state.get('earfcn_values', [])))
    )

    # Ввод MML примера/начала и конца
    mml_input = st.text_area("MML Example/Start")
    mml_input_end = ""
    if mml_type == "Cell LvL MML":
        mml_input_end = st.text_area("MML End (for Cell LvL MML)")

    # Кнопка для генерации примера входных данных
    if st.button("Сгенерировать пример входных данных"):
        generate_example()

    # Кнопка для генерации MML
    if st.button("Сгенерировать MML"):
        if not st.session_state.get('eNB_list_data'):
            st.error("Список eNB пуст.")
        else:
            generate_mml(mml_type, selected_earfcn, mml_input, mml_input_end)

def parse_data(data):
    parsed_data = []
    for line in data:
        if '\t' in line:
            parsed_data.append(line.split('\t'))
        elif ',' in line:
            parsed_data.append(line.split(','))
        elif ';' in line:
            parsed_data.append(line.split(';'))
        elif ' ' in line:
            parsed_data.append(line.split())
        else:
            parsed_data.append([line])
    return parsed_data

def update_counts():
    parsed_data = st.session_state['parsed_data']
    eNB_ids = set()
    for row in parsed_data:
        if row:
            eNB_ids.add(row[0])
    eNB_count = len(eNB_ids)
    cell_count = len(parsed_data)
    st.session_state['eNB_count'] = eNB_count
    st.session_state['cell_count'] = cell_count

def get_counts():
    return st.session_state.get('eNB_count', 0), st.session_state.get('cell_count', 0)

def update_earfcn_options():
    parsed_data = st.session_state['parsed_data']
    earfcn_values = set()
    for row in parsed_data:
        if len(row) > 2:
            earfcn_value = row[2]
            if isinstance(earfcn_value, str):
                earfcn_value = earfcn_value.strip()
            if str(earfcn_value).replace('.', '', 1).isdigit():
                earfcn_values.add(int(float(earfcn_value)))
    st.session_state['earfcn_values'] = earfcn_values

def generate_example():
    example_data = {
        "eNB_ID": ["AL7777", "AL8171", "AL7743"],
        "Cell_ID": [1, 11, 21],
        "DL_EARFCN": [1850, 1652, 500]
    }
    df = pd.DataFrame(example_data)
    csv = df.to_csv(index=False)
    st.download_button("Скачать пример входных данных", csv, "example.csv", "text/csv")

def generate_mml(mml_type, selected_earfcn_value, mml_input, mml_input_end):
    parsed_data = st.session_state['parsed_data']

    # Фильтрация по EARFCN
    if selected_earfcn_value != "All cells":
        parsed_data = [
            row for row in parsed_data
            if len(row) > 2 and str(int(float(row[2]))) == selected_earfcn_value
        ]

    output = []
    if mml_type == "eNB LvL MML":
        if not mml_input:
            st.error("MML пример пуст.")
            return
        output = [f"{mml_input}{{{row[0]}}}" for row in parsed_data if len(row) > 0]

    elif mml_type == "Cell LvL MML":
        if not mml_input or not mml_input_end:
            st.error("MML начало или конец пусты.")
            return
        for row in parsed_data:
            if len(row) >= 2:
                eNB, cell_id = row[:2]
                output.append(f"{mml_input}{cell_id}{mml_input_end}{{{eNB}}}")
            else:
                st.error(f"Неверный формат данных в строке: {row}")
                return

    if not output:
        st.error("Нет данных для генерации MML.")
        return

    # Объединение вывода в строку
    output_text = "\n".join(output)

    # Разбиение на части по 5MB
    parts = split_output(output_text, part_size_bytes=5 * 1024 * 1024)

    for i, part in enumerate(parts, 1):
        st.download_button(
            label=f"Скачать MML файл (часть {i})",
            data=part,
            file_name=f"mml_output_part_{i}.txt",
            mime="text/plain"
        )

def split_output(output_text, part_size_bytes):
    output_bytes = output_text.encode('utf-8')
    parts = []
    start = 0
    total_length = len(output_bytes)

    while start < total_length:
        end = min(start + part_size_bytes, total_length)
        # Находим последний перевод строки перед ограничением
        if end < total_length:
            newline_pos = output_bytes.rfind(b'\n', start, end)
            if newline_pos != -1 and newline_pos > start:
                end = newline_pos + 1
        parts.append(output_bytes[start:end].decode('utf-8'))
        start = end

    return parts

if __name__ == "__main__":
    main()
