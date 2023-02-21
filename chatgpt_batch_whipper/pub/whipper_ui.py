"""
MIT License

Copyright (c) 2023, CodeDigger

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

WhipperUI: A Streamlit UI control class
Author: CodeDigger
Date: 2023/02/19
Description: This module defines a UIControl class for Streamlit, which provides a consistent interface for creating and interacting with different types of UI controls. The class supports boolean, integer, float, and string data types.
Disclaimer: This software is provided "as is" and without any express or implied warranties, including, without limitation, the implied warranties of merchantability and fitness for a particular purpose. The author and contributors of this module shall not be liable for any direct, indirect, incidental, special, exemplary, or consequential damages (including, but not limited to, procurement of substitute goods or services; loss of use, data, or profits; or business interruption) however caused and on any theory of liability, whether in contract, strict liability, or tort (including negligence or otherwise) arising in any way out of the use of this software, even if advised of the possibility of such damage.
"""
import time

import streamlit as st
from st_aggrid import GridOptionsBuilder, AgGrid, JsCode
from datetime import datetime
import base64
import os
import csv
from PIL import Image
import pandas as pd
from .chatgpt_wrapper import ChatGPT


class WhipperUI:
    BOT = None
    TABLE_FONTSIZE = "17px"
    HOME_PATH = "./%s"
    WAITING_TIME = 10
    PROMPT_PATH = HOME_PATH % "prompt_master.csv"
    ICON_FILE = "icon.png"
    RESULT_FILE = HOME_PATH % "buff/"
    GPT_RESULT_COL = "result"
    GPT_INPUT_COL = "input"
    CHECK_COL = "Is false"
    COMMENT_COL = "Comment"
    INPUT_FOLD = HOME_PATH % "inputs"
    CHECKBOR_RENDDER = JsCode("""
       class CheckboxRenderer{

           init(params) {
               this.params = params;

               this.eGui = document.createElement('input');
               this.eGui.type = 'checkbox';
               this.eGui.checked = params.value;

               this.checkedHandler = this.checkedHandler.bind(this);
               this.eGui.addEventListener('click', this.checkedHandler);
           }

           checkedHandler(e) {
               let checked = e.target.checked;
               let colId = this.params.column.colId;
               this.params.node.setDataValue(colId, checked);
           }

           getGui(params) {
               return this.eGui;
           }

           destroy(params) {
           this.eGui.removeEventListener('click', this.checkedHandler);
           }
       }//end class
       """)

    DEFAULT_CELL_JS = JsCode("""
                        function(params) {
                                params.columnApi.autoSizeColumns();
                                if (params.data.hasOwnProperty('status')){
                                    if(params.data.status == 'Finished'){
                                        return {
                                            'color': 'black',
                                            'backgroundColor': 'green',
                                            'fontSize':'{fontSize}'
                                        }
                                    }
                                }

                                return {
                                    'color': 'black',
                                    'backgroundColor': 'white',
                                    'fontSize':'{fontSize}'
                                    }

                            }
                        """.replace("{fontSize}", TABLE_FONTSIZE))

    def _set_up_page(self):
        im = Image.open(self.HOME_PATH % self.ICON_FILE)
        STREAMLIT_AGGRID_URL = "https://github.com/PablocFonseca/streamlit-aggrid"
        st.set_page_config(
            layout="centered",
            page_icon=im,
            page_title="Moomin Rakuten Offical Shop Dashboard(By ECD)-Search scraping"
        )
        st.title("Chat GPT batch job")
        self._set_background(self.HOME_PATH % 'background.png')

    def __init__(self):
        self._set_up_page()
        return

    @staticmethod
    def _get_base64(bin_file):
        """
        Returns the Base64-encoded representation of a binary file.

        :param bin_file: the path to the binary file to encode
        :return: the Base64-encoded string
        """
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()

    def _set_background(self, png_file):
        """
        Sets the background image of the Streamlit app to the specified PNG file.

        :param png_file: the path to the PNG file to use as the background image
        """
        # Convert the PNG file to a Base64-encoded string
        bin_str = self._get_base64(png_file)

        # Define a CSS rule to set the background image of the app
        # to the Base64-encoded PNG file
        page_bg_img = '''
        <style>
        .stApp {
        background-color: pink !important;
        background-image: url("data:image/png;base64,%s");
        background-size: cover;
        }
        </style>

        ''' % bin_str

        # Apply the CSS rule to the Streamlit app
        st.markdown(page_bg_img, unsafe_allow_html=True)

    def _load_cache(self):
        """
        Loads the cache from the result file.

        :return: a pandas DataFrame containing the cache data, or None if the result file could not be loaded
        """
        try:
            # Try to load the result file as a pandas DataFrame
            return pd.read_csv(self.RESULT_FILE, index_col=False, encoding='utf-8-sig')
        except:
            # If there is an error, return None
            return None

    def _load_prompts(self):
        """
        Loads the prompts data from a CSV file.

        :return: a pandas DataFrame containing the prompts data
        """
        if os.path.isfile(self.PROMPT_PATH):
            # If the file exists, load the data as a pandas DataFrame
            prompts_df = pd.read_csv(self.PROMPT_PATH)
            prompts_df[["conversation_id", "parent_message_id"]].fillna("", inplace=True)
        else:
            # If the file doesn't exist, create an empty DataFrame with the default columns
            default_columns = ["Date", "No", "prompt", "conversation_id", "parent_message_id"]
            prompts_df = pd.DataFrame(columns=default_columns)

        return prompts_df

    def _create_table(self, data, check_col=None, comment_col=None, pagesize=100):
        """
        Creates an Ag-Grid table from a pandas DataFrame.

        :param data: the pandas DataFrame to use as the data source for the table
        :param comment_col: the name of the column to use for comments, if any
        """
        # Create an Ag-Grid options builder from the pandas DataFrame
        indexs = None
        if "index" in data.columns.values:
            indexs = data["index"]
            data.drop("index", axis=1, inplace=True)
        gb = GridOptionsBuilder.from_dataframe(data)

        # Configure the default column settings for the table
        gb.configure_default_column(
            min_column_width=120,  # Set the minimum column width to 120 pixels
            suppressMenu=True,  # Disable the column menu
            autoSizeColumns=True,  # Automatically size the columns to fit the data
            editable=False  # Make the cells non-editable
        )

        # Enable range selection for the table
        gb.configure_grid_options(enableRangeSelection=True)

        # Configure pagination settings for the table
        gb.configure_pagination(
            paginationPageSize=pagesize,  # Set the number of rows per page to 100
            paginationAutoPageSize=False  # Disable automatic pagination
        )
        if check_col is not None:
            gb.configure_column(check_col, editable=True, cellRenderer=self.CHECKBOR_RENDDER)
        if comment_col is not None:
            gb.configure_column(comment_col, editable=True)

        grid_options = gb.build()
        grid_options['getRowStyle'] = self.DEFAULT_CELL_JS
        result = AgGrid(data, gridOptions=grid_options, enable_enterprise_modules=True, allow_unsafe_jscode=True)[
            "data"]
        if indexs is not None:
            result["index"] = indexs
        return result

    def _load_result(self, result_no):
        """
        Loads the result data from a CSV file.

        :param result_no: the number of the result to load
        :return: a pandas DataFrame containing the result data
        """
        # Create the result file directory if it doesn't exist
        if not os.path.exists(self.RESULT_FILE):
            os.makedirs(self.RESULT_FILE)

        # Construct the file path for the specified result number
        file_path = os.path.join(self.RESULT_FILE, f"{result_no}.csv")

        if os.path.isfile(file_path):
            # If the file exists, load the data as a pandas DataFrame
            result_df = pd.read_csv(file_path)
        else:
            # If the file doesn't exist, create an empty DataFrame with the default columns
            default_columns = [self.GPT_RESULT_COL, self.GPT_INPUT_COL, self.CHECK_COL, self.COMMENT_COL]
            result_df = pd.DataFrame(columns=default_columns)

        return result_df

    @staticmethod
    def _list_prompts(prompts_df):
        """
        Lists the prompts from a pandas DataFrame and returns the selected prompt.

        :param prompts_df: the pandas DataFrame containing the prompts data
        :return: the selected prompt number
        """
        # Extract the prompt numbers from the DataFrame
        prompts_list = [no for no in prompts_df["No"]]

        # Display the prompts list in a Streamlit container
        st.markdown("### Prompts list:")
        placeholder = st.empty()
        placeholder.empty()
        with placeholder.container():
            # Allow the user to select a prompt from the list
            return st.selectbox('', prompts_list)

    def on_add(self, prompt, prompt_name):
        """
        Adds a new prompt to the prompts data and saves it to a CSV file.

        :param prompt: the prompt text to add
        :param prompt_name: the name of the prompt to add, if any
        """
        # Load the prompts data from the CSV file
        prompts_df = self._load_prompts()

        # Get the index of the new prompt
        index = len(prompts_df)

        if len(prompt_name) > 0:
            # If the prompt has a name, use it in the prompt number
            no = f"{prompt_name}_{index}"
        else:
            # Otherwise, use the index as the prompt number
            no = str(index)

        # Create a new row for the prompts DataFrame with the current date, prompt number, and prompt text
        new_row = {"Date": datetime.now().strftime('%Y-%m-%d'), "No": no, "prompt": prompt}

        # Add the new row to the top of the DataFrame
        prompts_df = pd.concat([pd.DataFrame(new_row, index=[0]), prompts_df]).reset_index(drop=True)

        # Save the updated prompts data to the CSV file
        prompts_df.to_csv(self.PROMPT_PATH, encoding='utf-8-sig', index=False)

    @staticmethod
    def reformat(text):
        """
        Replaces newline characters with a placeholder string.

        :param text: the text to reformat
        :return: the reformatted text
        """
        return text.replace("\n", "{pun}")

    @staticmethod
    def reformat_back(text):
        """
        Replaces a placeholder string with newline characters.

        :param text: the text to reformat
        :return: the reformatted text
        """
        return text.format(pun="\n")

    def on_set(self, prompt_no, prompt_text):
        """
        Sets a prompt text for a specified prompt number and saves it to a CSV file.

        :param prompt_no: the number of the prompt to set the text for
        :param prompt_text: the new text for the prompt
        """
        # Load the prompts data from the CSV file
        prompts_df = self._load_prompts()

        if len(prompts_df["No"] == prompt_no) == 0:
            # If the prompt number doesn't exist in the DataFrame, add a new prompt with the specified text
            self.on_add(prompt_text, prompt_name=prompt_no)
            return
        print(prompts_df)
        # Create a new row for the prompts DataFrame with the current date, prompt number, and prompt text
        new_row = prompts_df.loc[prompts_df["No"] == prompt_no]
        new_row["Date"] = datetime.now().strftime('%Y-%m-%d')
        new_row["prompt"] = prompt_text
        prompts_df = pd.concat([new_row, prompts_df[prompts_df["No"] != prompt_no]])
        # Save the updated prompts data to the CSV file
        prompts_df.to_csv(self.PROMPT_PATH, encoding='utf-8-sig', index=False)

    def on_delete_cache(self, result_no):
        """
        Deletes a cache file for a specified result number.

        :param result_no: the number of the result to delete the cache file for
        """
        cache_name = os.path.join(self.RESULT_FILE, f"{result_no}.csv")
        try:
            os.remove(cache_name)
        except OSError as error:
            print(f"An error occurred: {error}")

    def on_auth(self):
        """
        Deletes a cache file for a specified result number.

        :param result_no: the number of the result to delete the cache file for
        """
        ChatGPT(headless=False)

    def on_delete_prompt(self, prompt_no):
        """
        Deletes a prompt with a specified prompt number from the prompts data and saves the updated data to a CSV file.

        :param prompt_no: the number of the prompt to delete
        """
        # Load the prompts data from the CSV file
        prompts_df = self._load_prompts()

        # Remove the row with the specified prompt number from the DataFrame
        prompts_df = prompts_df[prompts_df["No"] != prompt_no]

        # Save the updated prompts data to the CSV file
        prompts_df.to_csv(self.PROMPT_PATH, encoding='utf-8-sig', index=False)

    @staticmethod
    def is_csv_format(s):
        try:
            _ = [_ for _ in csv.reader([s])]
            return True
        except csv.Error:
            return False

    def save_review_data(self, data, no):
        """
        Saves a DataFrame with checked results to a cache file.

        :param data: the DataFrame with checked results to save
        :param result_no: the number of the result to save the checked data for
        """
        cache_name = ("%s%s.csv") % (self.RESULT_FILE, no)
        data[self.CHECK_COL] = [True if s == True else False for s in data[self.CHECK_COL]]
        data.to_csv(cache_name, encoding='utf-8-sig', index=False)

    def _load_saved_input_data(self, selected_prompt_no):
        if selected_prompt_no is not None:
            try:
                return pd.read_csv("%s/input_%s.csv" % (self.INPUT_FOLD, selected_prompt_no))
            except:
                pass
        return None

    def _update_reviewdata(self, data_old, data_new):
        data_new = data_new[[self.CHECK_COL, self.COMMENT_COL]]
        result = data_old.join(data_new, how="left", rsuffix='_new')
        result = result.fillna("")
        new_checks = []
        new_comments = []
        new_check_col = self.CHECK_COL + '_new'
        new_comment_col = self.COMMENT_COL + '_new'
        for i, row in result.iterrows():
            if row[new_check_col] == row[new_check_col]:
                new_checks += [row[new_check_col]]
            else:
                new_checks += [row[self.CHECK_COL]]
            if row[new_comment_col] == row[new_comment_col]:
                new_comments += [row[new_comment_col]]
            else:
                new_comments += [row[self.COMMENT_COL]]
        result[self.CHECK_COL] = new_checks
        result[self.COMMENT_COL] = new_comments
        result = result.drop([new_check_col, new_comment_col], axis=1)
        return result

    def _submit(self, prompt, conversation_id, parent_message_id):
        res = self.BOT.ask(prompt)
        failed = False
        while res is None:
            st.error("Process failed  will resubmit it after %d minutes" % (self.WAITING_TIME // 60))
            st.empty()
            time.sleep(self.WAITING_TIME)
            self.BOT.reset()
            res = self.BOT.ask(prompt,
                               conversation_id,
                               parent_message_id)
            failed = True
        if failed:
            st.success("Process resumed!")
        return res

    def on_do(self, prompt_id, data, target_column, no_explain, do_false_only):
        """
        Uses the ChatGPT API to generate responses for prompts in a DataFrame.

        :param prompt: the prompt text to use for generating responses
        :param prompt_id: the id of the prompt
        :param conversation_id: the id of the conversation
        :param data: the DataFrame with prompts to generate responses for
        :param target_column: the column of the DataFrame with the prompts to use for generating responses
        :param no_explain: whether to prompt the user to avoid including explanations in their responses
        """
        if self.BOT is None:
            with st.spinner('Wait for connect to chatGPT...'):
                self.BOT = ChatGPT()
        prompts_df = self._load_prompts()
        setting = prompts_df[prompts_df["No"] == prompt_id]

        if len(setting) == 1:
            prompt = setting['prompt'].values[0]
            conversation_id = setting['conversation_id'].values[0]
            parent_message_id = setting['parent_message_id'].values[0]
        else:
            st.error("There is multiple prompts but currently we can only do one.")
            return
        if len(prompt) == 0:
            st.error("There is no prompt to do.")

        cache_name = ("%s%s.csv") % (self.RESULT_FILE, prompt_id)
        processed_data = self._load_result(prompt_id)
        if do_false_only:
            progress_bar = st.progress(0)
            condition = processed_data[self.CHECK_COL] == True
            row_indexs = processed_data[condition].index
            i = 0
            num = len(row_indexs)
            for row_index in row_indexs:
                progress_bar.progress(i * 100 // num)
                prompt_text = "%s\n\t\t%s" % (prompt, processed_data.at[row_index, self.GPT_INPUT_COL])
                processed_data.at[row_index, self.GPT_RESULT_COL] = self._submit(prompt_text, conversation_id,
                                                                                 parent_message_id)
                processed_data.to_csv(cache_name, encoding='utf-8-sig', index=False)
                i += 1
            return
        if data is not None and target_column is not None:
            prompts_inputs = [text for text in data[target_column]]
        else:
            prompts_inputs = [""]

        if data is not None:
            num = len(data)
            i = len(processed_data)
        else:
            num = 1
            i = 0
        bar_index = i * 100 // num
        progress_bar = st.progress(bar_index)
        for prompts_input in prompts_inputs[i: ]:
            prompt_text = "%s\n\t\t%s" % (prompt, prompts_input)
            res = self._submit(prompt_text, conversation_id, parent_message_id)
            conversation_id = self.BOT.get_conversation_id()
            parent_message_id = self.BOT.get_parent_message_id()
            if no_explain and not self.is_csv_format(res):
                prompt_text = "Do not include any explanation in your reply, please redo the \n\t\t%s." % prompts_input
                res = self._submit(prompt_text, conversation_id, parent_message_id)
            new_s = i * 100 // num
            if new_s > bar_index:
                progress_bar.progress(bar_index)
                bar_index = new_s
            i += 1
            new_row = pd.DataFrame([[prompts_input, res]], columns=[self.GPT_INPUT_COL, self.GPT_RESULT_COL])
            processed_data = pd.concat([processed_data, new_row],
                                       ignore_index=True)
            processed_data.to_csv(cache_name, encoding='utf-8-sig', index=False)
            # Create a new row for the prompts DataFrame with the current date, prompt number, and prompt text
        new_row = {"Date": datetime.now().strftime('%Y-%m-%d'),
                   "No": prompt_id,
                   "prompt": prompt,
                   "conversation_id": conversation_id,
                   "parent_message_id": parent_message_id
                   }
        # Update the row with the new prompt text in the DataFrame
        prompts_df.loc[prompts_df["No"] == prompt_id] = list(new_row.values())
        # Save the updated prompts data to the CSV file
        prompts_df.to_csv(self.PROMPT_PATH, encoding='utf-8-sig', index=False)
        progress_bar.empty()

    def show_prompt_ui(self):
        prompts_df = self._load_prompts()
        selected_prompt_no = self._list_prompts(prompts_df)
        setting = prompts_df[prompts_df["No"] == selected_prompt_no]
        setting = setting[["prompt"]]
        if len(setting) > 0:
            setting = setting.iloc[0, :].tolist()
            prompt_default = setting[0]

        else:
            prompt_default = ""
        st.markdown("##### Mode")
        mode = st.radio("", ('Single shoot', 'Fully Automatic(Batch job)'))
        uploaded_file = None
        no_explain = False
        if mode == 'Fully Automatic(Batch job)':
            file_select, no_explain_check = st.columns([3, 1])
            no_explain = no_explain_check.checkbox("No explanation in the reply", value=True,
                                                   key=None)
            uploaded_file = file_select.file_uploader("Select a CSV file")
        result_data = self._load_result(selected_prompt_no)
        data = self._load_saved_input_data(selected_prompt_no)
        prompt_name_title, select_column_title = st.columns(2)
        prompt_name_input, select_column = st.columns(2)
        target_column = None
        if uploaded_file is not None:
            if ".CSV" in uploaded_file.name.upper():
                try:
                    uploaded_file.name
                    data = pd.read_csv(uploaded_file)
                    if selected_prompt_no is not None:
                        data.to_csv("%s/input_%s.csv" % (self.INPUT_FOLD, selected_prompt_no), index=False)
                except:
                    pass

            else:
                st.error("Only CSV files are supported currently.")
        if data is not None:
            select_column_title.markdown("##### Select column you want to process")
            target_column = select_column.selectbox(
                '',
                data.columns.values)
        prompt_name_title.markdown("##### Please name you prompt")
        prompt_name = prompt_name_input.text_input('',
                                                   "prompt")
        st.markdown("##### Please write you prompt")
        prompt = st.text_area('',
                              prompt_default,
                              height=200)
        auth_bth, add_btn, process_btn, = st.columns(3)
        set_btn, delete_btn_cache, delete_btn_prompt = st.columns(3)
        download_btn, _ = st.columns(2)
        add_btn.button('Add',
                       on_click=self.on_add,
                       args=(prompt, prompt_name))
        set_btn.button('Update',
                       on_click=self.on_set,
                       args=(selected_prompt_no,
                             prompt))

        delete_btn_prompt.button('Delete Prompt',
                                 on_click=self.on_delete_prompt,
                                 args=(selected_prompt_no,))

        delete_btn_cache.button('Delete Cached result',
                                on_click=self.on_delete_cache,
                                args=(selected_prompt_no,))
        auth_bth.button('Auth',
                        on_click=self.on_auth,
                        args=())
        st.markdown("[Go to chatGPT](https://chat.openai.com/chat)")
        if data is not None:
            st.markdown("### The input data ")
            self._create_table(data, pagesize=10)
        show_false_only = False
        if len(result_data) > 0:
            st_title, show_false_only_cb = st.columns(2)
            st_title.markdown("### The processed result")
            show_false_only = show_false_only_cb.checkbox("Show only false data", value=False)
            result_data = result_data[[self.GPT_INPUT_COL, self.GPT_RESULT_COL, self.CHECK_COL, self.COMMENT_COL]]
            result_data.reset_index(inplace=True)
            if show_false_only:
                data_table = result_data[result_data[self.CHECK_COL]]
            else:
                data_table = result_data
            data_review = self._create_table(data_table, self.CHECK_COL, self.COMMENT_COL)
            result_data = self._update_reviewdata(result_data, data_review)
            download_btn.download_button(
                label="Download",
                data=result_data.to_csv().encode('utf-8'),
                file_name="%s.csv" % (selected_prompt_no),
                mime='text/csv')
            self.save_review_data(result_data, selected_prompt_no)

        process_btn.button('Submit',
                           on_click=self.on_do,
                           args=(selected_prompt_no,
                                 data,
                                 target_column,
                                 no_explain,
                                 show_false_only))
