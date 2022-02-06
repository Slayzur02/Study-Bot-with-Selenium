from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import urllib.request, json
import time
import requests
import sys
import simpleaudio as sa
import random as random



# TODO:
# refactor so you don't have to use global variables and global. 
# test it out
# create a function that puts in the answers for me!


# plays music, will be used if there is a problem when filling in the questions
def call_music(filename):
    wave_obj = sa.WaveObject.from_wave_file(filename)
    for _ in range(2):
        play_obj = wave_obj.play()
        play_obj.wait_done()  # Wait until sound has finished playing


# store into questions_and_answer
class q_and_a:
    def __init__(self, questionID, question_text, answer_dictionary):
        self.questionID = questionID
        self.question_text = question_text
        self.answer_dictionary = answer_dictionary
    
    def set_questionID(self, questionID):
        self.questionID = questionID
    
    def set_question_text(self, question_text):
        self.question_text = question_text
    
    def set_answer_dictionary(self, answer_dictionary):
        self.answer_dictionary = answer_dictionary

# store answers in q_and_a
class answer:
    def __init__(self,answerID, answer_text, correct):
        self.answerID = answerID
        self.answer_text = answer_text
        self.correct = correct

    def set_answerID(self, answerID):
        self.answerID = answerID

    def set_answer_text(self, answer_text):
        self.answer_text = answer_text

    def set_correct(self, correct):
        self.correct = correct


# store for testing_list
class testing_q_and_a:
    def __init__(self, questionID, answerID):
        self.test_questionID = questionID
        self.test_answerID = answerID
    def set_test_questionID(self, questionID):
        self.test_questionID = questionID
    def set_test_answerID(self, answerID):
        self.test_answerID = answerID




class study_bot:
    #is shared between instances so that I can create a second bot that uses the answers from the first bot.
    #holds q_and_a, update after every test
    questions_and_answers = {
        # questionID: {
        #   "questionID": questionID,
        #   "question_text": question_text,
        #   "answer_dictionary": {
        #       answerID: {
        #           "answerID",
        #           "answer_text",
        #           "correct"
        #       }
        # }    
        # }
    } 
    def __init__(self, username, password, site_url, test_id, filename, bugged, testing_list, time_range):
        self.username = username
        self.password = password
        self.site_url = site_url
        self.test_id = test_id
        self.filename = filename
        self.bugged = bugged
        self.time_range = time_range

        #holds testing_q_and_a, is looped through to update questions_and_answers
        self.testing_list = testing_list
        
        _browser_profile = webdriver.FirefoxProfile()
        # Make no notifications pop-up, which can stop certain buttons
        _browser_profile.set_preference("dom.webnotifications.enabled", False)
        self.bot = webdriver.Firefox(firefox_profile=_browser_profile)

    def login(self):
        bot = self.bot
        bot.get("http://study.hanoi.edu.vn/dang-nhap?returnUrl=/")
        time.sleep(3)
        site_username = bot.find_element_by_id('UserName')
        site_password = bot.find_element_by_id('Password')
        site_login_click = bot.find_element_by_id('AjaxLogin')
        site_username.clear()
        site_password.clear()
        site_username.send_keys(self.username)
        site_password.send_keys(self.password)
        site_login_click.send_keys(Keys.RETURN)

    def reset_testing_list(self):
        self.testing_list = []

    def get_into_test(self):
        bot = self.bot
        bot.get("http://study.hanoi.edu.vn/")
        time.sleep(5)
        bot.get(self.site_url)
        time.sleep(5)
        site_vao_thi_button = bot.find_element_by_css_selector('.btn.btn-primary')
        site_vao_thi_button.send_keys(Keys.RETURN)
        time.sleep(5)
        site_bat_dau_lam_bai_button = bot.find_element_by_css_selector('.btn.btn-warning.btn-start-test')
        site_bat_dau_lam_bai_button.send_keys(Keys.RETURN)

    # Puts all the questions and answers into a map
    def query_questions_and_answers(self):
        bot = self.bot
        questions_and_answers_list = bot.find_elements_by_css_selector('.question-box')
        for question_and_answer in questions_and_answers_list:
            #get the question ID and store into q_and_a instance
            q_and_a_instance = q_and_a("","",{})
            questionID = question_and_answer.get_attribute("id")
            q_and_a_instance.set_questionID(questionID)

            #get the question Text and store into q_an_a instance
            question_text_element = question_and_answer.find_element_by_css_selector('.col-11')
            question = question_text_element.text
            q_and_a_instance.set_question_text(question)

            # (use for) get the answerID - answerText and store them into answer dictionary and store answer_dic to q_and_a_dictionary
            answer_elements = question_and_answer.find_elements_by_css_selector('.col-md-6')
            for answer_element in answer_elements:
                answer_instance = answer("", "", "")
                # get answer ID
                answer_id_element = answer_element.find_element_by_tag_name('input')
                answerID = answer_id_element.get_attribute("id")
                answer_instance.set_answerID(answerID)

                # get answer text
                answer_text_element = answer_element.find_element_by_css_selector('.col-10')
                answer_text = answer_text_element.text
                answer_instance.set_answer_text(answer_text)

                q_and_a_instance.answer_dictionary[answer_instance.answerID] = {
                    "answerID": answer_instance.answerID,
                    "answer_text": answer_instance.answer_text,
                    "correct": "",
                }

            # store to questions_and_answers
            if q_and_a_instance.questionID in study_bot.questions_and_answers:
                continue
            else:
                study_bot.questions_and_answers[q_and_a_instance.questionID] = {
                    "questionID": q_and_a_instance.questionID,
                    "question_text": q_and_a_instance.question_text,
                    "answer_dictionary": q_and_a_instance.answer_dictionary,
                    "correct_answer_id": "",
                }
            
        

    def choose_answers_and_submit(self):
        bot = self.bot
        questions_and_answers_list = bot.find_elements_by_css_selector('.question-box')

        # Use for loop to get all the elements of the questions
        for question_and_answer in questions_and_answers_list:

            # scroll into question so I can click it
            question_and_answer.location_once_scrolled_into_view

            # get questionID
            testing_q_and_a_instance = testing_q_and_a("", "")
            questionID = question_and_answer.get_attribute("id")
            testing_q_and_a_instance.set_test_questionID(questionID)

            # get all the answer elements
            answer_elements = question_and_answer.find_elements_by_css_selector('.col-md-6')

            # if the question already has an answer - choose the correct answer:
            if study_bot.questions_and_answers[questionID]["correct_answer_id"] != "":
                correct_answer_id = study_bot.questions_and_answers[questionID]["correct_answer_id"]
                for answer_element in answer_elements:
                    answer_id_element = answer_element.find_element_by_tag_name('input')
                    answerID = answer_id_element.get_attribute("id")
                    if answerID != correct_answer_id:
                        continue
                    else:
                        answer_id_element.location_once_scrolled_into_view
                        answer_id_element.click() 
                        testing_q_and_a_instance.set_test_answerID(answerID)
                        break

            # if it does not have an answer, choose the one that hasn't been checked, a.k.a correct = false
            else:
                for answer_element in answer_elements:
                    answer_id_element = answer_element.find_element_by_tag_name('input')
                    answerID = answer_id_element.get_attribute("id")
                    if study_bot.questions_and_answers[questionID]["answer_dictionary"][answerID]["correct"] != "":
                        continue
                    else:
                        answer_id_element.location_once_scrolled_into_view
                        answer_id_element.click()
                        testing_q_and_a_instance.set_test_answerID(answerID)
                        break
            
            # Append to the test_list with dictionary as above

            self.testing_list.append({
                "test_questionID": testing_q_and_a_instance.test_questionID,
                "test_answerID": testing_q_and_a_instance.test_answerID,
                "correct": False,
            })


        time.sleep(1)
        # Scroll to the "Submit" button
        bot.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        nop_bai_button = bot.find_element_by_css_selector('.btn.btn-warning')
        nop_bai_button.click()
        time.sleep(1)

        dong_y_button = bot.find_element_by_css_selector('.swal2-confirm')
        dong_y_button.send_keys(Keys.RETURN)
        
    
    def reflect_answers(self):
        bot = self.bot
        
        # Retrieve the json in http://study.hanoi.edu.vn/home/scoreajax?id=447&rt=1 using request
        cookies = bot.get_cookies()
        s = requests.Session()
        for cookie in cookies:
            s.cookies.set(cookie['name'], cookie['value'])
        r = s.get('http://study.hanoi.edu.vn/home/scoreajax?id='+self.test_id+'&rt=1')
        if r.status_code == 200:
            true_answers_list = r.json()['TrueAnswer'].split(',')

        # changes all "correct" = True based on the index of the list
        def return_index(ket_qua_string): 
            string_number_with_dot = ket_qua_string.strip().split(' ')[1]
            number = int(string_number_with_dot[:-1])
            return number-1
        true_answers_index = list(map(return_index, true_answers_list))

        for i in true_answers_index:
            self.testing_list[i]["correct"] = True
        
        # Update the questions_and_answers based on testing_list
        for node in self.testing_list:
            if node["correct"]: 
                correct_questionID = node["test_questionID"]

                if study_bot.questions_and_answers[correct_questionID]["correct_answer_id"] == "":
                    study_bot.questions_and_answers[correct_questionID]["correct_answer_id"] = node["test_answerID"]
                    study_bot.questions_and_answers[correct_questionID]["answer_dictionary"][node["test_answerID"]]["correct"] = "true"
                if correct_questionID in self.bugged:
                    self.bugged.remove(correct_questionID)
            else: 
                wrong_questionID = node["test_questionID"]
                if study_bot.questions_and_answers[wrong_questionID]["correct_answer_id"] == "":
                    study_bot.questions_and_answers[wrong_questionID]["answer_dictionary"][node["test_answerID"]]["correct"] = "false"
                    

        sys.stdout.flush()


    def identify_bugged_questions(self):
        self.bugged = []
        for val in study_bot.questions_and_answers.values():
            if val["correct_answer_id"] == "":
                for v in val["answer_dictionary"].values():
                    v["correct"] = ""
                self.bugged.append(v["questionID"])
    
    def fix_bugged_questions(self):
        bot = self.bot
        questions_and_answers_list = bot.find_elements_by_css_selector('.question-box')

        for question_and_answer in questions_and_answers_list:
            question_and_answer.location_once_scrolled_into_view

            # get questionID
            testing_q_and_a_instance = testing_q_and_a("", "")
            questionID = question_and_answer.get_attribute("id")
            if questionID not in self.bugged:
                continue
            
            testing_q_and_a_instance.set_test_questionID(questionID)

            # get all the answer elements
            answer_elements = question_and_answer.find_elements_by_css_selector('.col-md-6')

            # It does not have an answer, choose the one that hasn't been checked, a.k.a correct = false
            for answer_element in answer_elements:
                answer_id_element = answer_element.find_element_by_tag_name('input')
                answerID = answer_id_element.get_attribute("id")
                if study_bot.questions_and_answers[questionID]["answer_dictionary"][answerID]["correct"] != "":
                    continue
                else:
                    answer_id_element.click()
                    testing_q_and_a_instance.set_test_answerID(answerID)
                    break
            
            # Append to the test_list with dictionary as above
            self.testing_list.append({
                "test_questionID": testing_q_and_a_instance.test_questionID,
                "test_answerID": testing_q_and_a_instance.test_answerID,
                "correct": False,
            })


        time.sleep(1)
        # Scroll to the "Submit" button
        # bot.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.HOME)
        bot.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)


        nop_bai_button = bot.find_element_by_css_selector('.btn.btn-warning')
        nop_bai_button.click()
        time.sleep(1)

        dong_y_button = bot.find_element_by_css_selector('.swal2-confirm')
        dong_y_button.send_keys(Keys.RETURN)


    # Called once we have a question map. Tests and re-evaluates.
    def final_check(self):
        bot = self.bot
        wrong_questions = []

        for _ in range(3):
            time.sleep(10)
            self.testing_list = []
            self.get_into_test()
            time.sleep(10)
            
            self.choose_answers_and_submit()
            time.sleep(10)
        
            # Retrieve the json in http://study.hanoi.edu.vn/home/scoreajax?id=self.test_id&rt=1 using request
            cookies = bot.get_cookies()
            s = requests.Session()
            for cookie in cookies:
                s.cookies.set(cookie['name'], cookie['value'])
            r = s.get('http://study.hanoi.edu.vn/home/scoreajax?id='+self.test_id+'&rt=1')
            if r.status_code == 200:
                wrong_answers_list = r.json()['FalseAnser'].split(',')

            # checks if there are no wrong answers (a.k.a wrong_answer_list = [''])
            if wrong_answers_list[0] == '':
                continue

            # there are wrong answers, so push the questions IDs into the wrong_questions list
            def return_index(ket_qua_string): 
                string_number_with_dot = ket_qua_string.strip().split(' ')[1]
                number = int(string_number_with_dot[:-1])
                return number-1
            wrong_answers_index = list(map(return_index, wrong_answers_list))

            for i in wrong_answers_index:
                wrong_questions.append(self.testing_list[i]["test_questionID"])
            time.sleep(10)

        # if no wrong question appears at least twice (out of three times) - it's fine
        if len(wrong_questions) == len(set(wrong_questions)):
            return False
        # else, push it into bugged_questions and call fix_bugged_questions to solve
        else:
            for node in wrong_questions:
                wrong_questions.remove(node)
                if node in wrong_questions:
                    self.bugged.append(node)
                    while node in wrong_questions:
                        wrong_questions.remove(node)
            while len(self.bugged) > 0:
                self.testing_list = []
                self.fix_bugged_questions()
                self.reflect_answers()
            return True
    

    def log_the_answers(self):
        file=open(self.filename+".txt", "w+")
        i=0
        for value in study_bot.questions_and_answers.values():
            question_text = value["question_text"]
            j=0
            list_of_choices = ["", "", "", ""]
            for v in value["answer_dictionary"].values():
                j+=1
                list_of_choices[j-1] = v["answer_text"]
            answer_text = value["answer_dictionary"][value["correct_answer_id"]]["answer_text"]
            answerID =value["answer_dictionary"][value["correct_answer_id"]]["answerID"] 
            i += 1
            file.write(f"Cau hoi {i}: \n {question_text} \nLua chon 1:{list_of_choices[0]}\nLua chon 2:{list_of_choices[1]}\nLua chon 3:{list_of_choices[2]}\nLua chon 4: {list_of_choices[3]}\n    Cau tra loi: {answer_text} \n    answerID: {answerID}  \n \n \n")
        file.close()

    def destroy_self(self):
        bot = self.bot
        bot.quit()

    def answering_test(self):
        bot = self.bot
        questions_and_answers_list = bot.find_elements_by_css_selector('.question-box')

        # Use for loop to get all the elements of the questions
        for question_and_answer in questions_and_answers_list:

            # scroll into question so I can click it
            question_and_answer.location_once_scrolled_into_view

            # get questionID
            questionID = question_and_answer.get_attribute("id")

            # get all the answer elements
            answer_elements = question_and_answer.find_elements_by_css_selector('.col-md-6')

            # if the question already has an answer - choose the correct answer:
            if study_bot.questions_and_answers[questionID]["correct_answer_id"] != "":
                correct_answer_id = study_bot.questions_and_answers[questionID]["correct_answer_id"]
                for answer_element in answer_elements:
                    answer_id_element = answer_element.find_element_by_tag_name('input')
                    answerID = answer_id_element.get_attribute("id")
                    if answerID != correct_answer_id:
                        continue
                    else:
                        answer_id_element.location_once_scrolled_into_view
                        answer_id_element.click() 
                        break

            # if it does not have an answer, alert with bug and open music file.
            else:
                print("THERE WAS A BUG - returning...")
                call_music("beep_warning.wav")
                time.sleep(300)

        random_wait_time = random.randint(60*self.time_range[0], 60*self.time_range[1])
        print("RANDON WAIT TIME:" + str(random_wait_time))
        time.sleep(random_wait_time)
        # Scroll to the "Submit" button
        bot.execute_script("window.scrollTo(0, 0);")
        time.sleep(3)

        nop_bai_button = bot.find_element_by_css_selector('.btn.btn-warning')
        nop_bai_button.click()
        time.sleep(3)

        dong_y_button = bot.find_element_by_css_selector('.swal2-confirm')
        dong_y_button.send_keys(Keys.RETURN)

# This is the original code that runs only once. Has been refactored into the function below  

# create_study_bot = study_bot("0116375120", "0116375120", "http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-lich-su-12-e-so-5-402", "402", "lich-su-hk2-de-5", [])
# create_study_bot.login()
# time.sleep(1)
# create_study_bot.get_into_test()
# time.sleep(6)
# create_study_bot.query_questions_and_answers()
# time.sleep(4)
# create_study_bot.choose_answers_and_submit()
# time.sleep(10)
# create_study_bot.reflect_answers()
# time.sleep(6)

# create_study_bot.reset_testing_list()
# create_study_bot.get_into_test()
# time.sleep(6)
# create_study_bot.choose_answers_and_submit()
# time.sleep(10)
# create_study_bot.reflect_answers()
# time.sleep(6)


# create_study_bot.reset_testing_list()
# create_study_bot.get_into_test()
# time.sleep(6)
# create_study_bot.choose_answers_and_submit()
# time.sleep(10)
# create_study_bot.reflect_answers()
# time.sleep(6)

# create_study_bot.reset_testing_list()
# create_study_bot.get_into_test()
# time.sleep(6)
# create_study_bot.choose_answers_and_submit()
# time.sleep(10)
# create_study_bot.reflect_answers()
# time.sleep(6)
# create_study_bot.reset_testing_list()

# create_study_bot.identify_bugged_questions()
# while len(create_study_bot.bugged) > 0:
#     "THERE WAS A BUGG"
#     create_study_bot.reset_testing_list()
#     create_study_bot.fix_bugged_questions()
#     create_study_bot.reflect_answers()

# while create_study_bot.final_check():
#     pass


# create_study_bot.log_the_answers()



def giai_de(site, id, filename, time_range):
    try:
        study_bot.questions_and_answers = {}
        create_study_bot = study_bot("0116375120", "0116375120", site, id, filename, [], [], time_range)
        create_study_bot.login()
        time.sleep(10)
        create_study_bot.get_into_test()
        time.sleep(6)
        create_study_bot.query_questions_and_answers()
        time.sleep(4)
        create_study_bot.choose_answers_and_submit()
        time.sleep(10)
        create_study_bot.reflect_answers()
        time.sleep(6)

        create_study_bot.reset_testing_list()
        create_study_bot.get_into_test()
        time.sleep(6)
        create_study_bot.choose_answers_and_submit()
        time.sleep(10)
        create_study_bot.reflect_answers()
        time.sleep(6)


        create_study_bot.reset_testing_list()
        create_study_bot.get_into_test()
        time.sleep(6)
        create_study_bot.choose_answers_and_submit()
        time.sleep(10)
        create_study_bot.reflect_answers()
        time.sleep(6)

        create_study_bot.reset_testing_list()
        create_study_bot.get_into_test()
        time.sleep(6)
        create_study_bot.choose_answers_and_submit()
        time.sleep(10)
        create_study_bot.reflect_answers()
        time.sleep(6)
        create_study_bot.reset_testing_list()

        create_study_bot.identify_bugged_questions()
        while len(create_study_bot.bugged) > 0:
            create_study_bot.reset_testing_list()
            create_study_bot.fix_bugged_questions()
            create_study_bot.reflect_answers()

        # calls final_check till everything is correct (or "almost" correct)
        while create_study_bot.final_check():
            pass

        # create_study_bot.log_the_answers()

        time.sleep(5)
        

        answering_study_bot = study_bot("0116375165", "0116375165", site, id, "dont-use", [], [], time_range)
        answering_study_bot.login()
        time.sleep(5)
        answering_study_bot.get_into_test()
        time.sleep(10)
        answering_study_bot.answering_test()
        time.sleep(14)

        # create_study_bot.destroy_self()
        # answering_study_bot.destroy_self()

    except Exception as e: 
        print("A random error occured")
        call_music("beep_warning.wav")
        print(e)



#tieng anh
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-tieng-anh-12-e-so-1-474", "474", "tieng-anh-hk2-de-1", [30,40])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-tieng-anh-12-e-so-2-475", "475", "tieng-anh-hk2-de-2", [40,53])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-tieng-anh-12-e-so-2-476", "476", "tieng-anh-hk2-de-3", [35,48])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-tieng-anh-12-e-so-2-477", "477", "tieng-anh-hk2-de-4", [30,40])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-tieng-anh-12-e-so-2-478", "478", "tieng-anh-hk2-de-5", [24, 50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-tieng-anh-12-e-so-2-479", "479", "tieng-anh-hk2-de-6", [40, 55])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-tieng-anh-12-e-so-2-480", "480", "tieng-anh-hk2-de-7", [40, 55])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-tieng-anh-12-e-so-2-481", "481", "tieng-anh-hk2-de-8", [40, 55])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-tieng-anh-12-e-so-2-482", "482", "tieng-anh-hk2-de-9", [40, 55])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-tieng-anh-12-e-so-2-483", "483", "tieng-anh-hk2-de-10", [40, 55])


# hoa hoc
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-hoa-hoc-12-e-so-1-445", "445", "hoc-hoc-hk2-de-1", [15, 20])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-hoa-hoc-12-e-so-2-446", "446", "hoc-hoc-hk2-de-2", [20, 25])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-hoa-hoc-12-e-so-3-447", "447", "hoa-hoc-hk2-de-3", [20, 27])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-hoa-hoc-12-e-so-4-448", "448", "hoa-hoc-hk2-de-4", [20, 24])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-hoa-hoc-12-e-so-5-449", "449", "hoa-hoc-hk2-de-5", [20, 24])

# sinh hoc
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-sinh-hoc-12-e-so-1-368", "368", "sinh-hoc-hk2-de-1", [18,27])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-sinh-hoc-12-e-so-2-369", "369", "sinh-hoc-hk2-de-2", [18,27])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-sinh-hoc-12-e-so-3-370", "370", "sinh-hoc-hk2-de-3", [18,27])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-sinh-hoc-12-e-so-4-371", "371", "sinh-hoc-hk2-de-4", [18,27])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-sinh-hoc-12-e-so-5-372", "372", "sinh-hoc-hk2-de-5", [18,27])

#lich su
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-lich-su-12-e-so-1-398", "398", "lich-su-hk2-de-1", [18,27])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-lich-su-12-e-so-2-399", "399", "lich-su-hk2-de-2", [18,27])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-lich-su-12-e-so-3-400", "400", "lich-su-hk2-de-3", [18,27])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-lich-su-12-e-so-4-401", "401", "lich-su-hk2-de-4", [18,27])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-lich-su-12-e-so-5-402", "402", "lich-su-hk2-de-5", [18,27])

#dia li
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-ia-li-12-e-so-1-378", "378", "dia-li-hk2-de-1", [18,27])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-ia-li-12-e-so-2-379", "379", "dia-li-hk2-de-2", [18,27])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-ia-li-12-e-so-3-380", "380", "dia-li-hk2-de-3", [18,27])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-ia-li-12-e-so-4-381", "381", "dia-li-hk2-de-4", [18,27])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-ia-li-12-e-so-5-382", "382", "dia-li-hk2-de-5", [18,27])

#gdcd
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-gdcd-12-e-so-1-409", "409", "gdcd-hk2-de-1", [18,27])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-gdcd-12-e-so-2-410", "410", "gdcd-hk2-de-2", [18,27])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-gdcd-12-e-so-3-411", "411", "gdcd-hk2-de-3", [18,27])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-gdcd-12-e-so-4-412", "412", "gdcd-hk2-de-4", [18,27])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-hk2-mon-gdcd-12-e-so-5-413", "413", "gdcd-hk2-de-5", [18,27])

# lich su MOI
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-lich-su-12-e-so-01-696", "696", "lich-su-MOI-de-01", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-lich-su-12-e-so-19-697", "697", "lich-su-MOI-de-19", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-lich-su-12-e-so-20-698", "698", "lich-su-MOI-de-20", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-lich-su-12-e-so-02-699", "699", "lich-su-MOI-de-02", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-lich-su-12-e-so-03-700", "700", "lich-su-MOI-de-03", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-lich-su-12-e-so-04-701", "701", "lich-su-MOI-de-04", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-lich-su-12-e-so-05-702", "702", "lich-su-MOI-de-05", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-lich-su-12-e-so-06-703", "703", "lich-su-MOI-de-06", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-lich-su-12-e-so-07-704", "704", "lich-su-MOI-de-07", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-lich-su-12-e-so-08-705", "705", "lich-su-MOI-de-08", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-lich-su-12-e-so-09-706", "706", "lich-su-MOI-de-09", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-lich-su-12-e-so-10-707", "707", "lich-su-MOI-de-10", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-lich-su-12-e-so-11-688", "688", "lich-su-MOI-de-11", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-lich-su-12-e-so-12-689", "689", "lich-su-MOI-de-12", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-lich-su-12-e-so-13-690", "690", "lich-su-MOI-de-13", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-lich-su-12-e-so-14-691", "691", "lich-su-MOI-de-14", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-lich-su-12-e-so-15-692", "692", "lich-su-MOI-de-15", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-lich-su-12-e-so-16-693", "693", "lich-su-MOI-de-16", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-lich-su-12-e-so-17-694", "694", "lich-su-MOI-de-17", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-lich-su-12-e-so-18-695", "695", "lich-su-MOI-de-18", [40,50])



# sinh hoc MOI
giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-sinh-hoc-12-e-so-01-633", "633", "sinh-hoc-MOI-de-01", [30,40])
# broken link
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-sinh-hoc-12-e-so-02-634", "634", "sinh-hoc-MOI-de-02", [40,50]) broken link
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-sinh-hoc-12-e-so-03-635", "635", "sinh-hoc-MOI-de-03", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-sinh-hoc-12-e-so-04-636", "636", "sinh-hoc-MOI-de-04", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-sinh-hoc-12-e-so-05-637", "637", "sinh-hoc-MOI-de-05", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-sinh-hoc-12-e-so-06-638", "638", "sinh-hoc-MOI-de-06", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-sinh-hoc-12-e-so-07-639", "639", "sinh-hoc-MOI-de-07", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-sinh-hoc-12-e-so-08-640", "640", "sinh-hoc-MOI-de-08", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-sinh-hoc-12-e-so-09-641", "641", "sinh-hoc-MOI-de-09", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-sinh-hoc-12-e-so-10-642", "642", "sinh-hoc-MOI-de-10", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-sinh-hoc-12-e-so-11-643", "643", "sinh-hoc-MOI-de-11", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-sinh-hoc-12-e-so-12-644", "644", "sinh-hoc-MOI-de-12", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-sinh-hoc-12-e-so-13-646", "646", "sinh-hoc-MOI-de-13", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-sinh-hoc-12-e-so-14-647", "647", "sinh-hoc-MOI-de-14", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-sinh-hoc-12-e-so-15-648", "648", "sinh-hoc-MOI-de-15", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-sinh-hoc-12-e-so-16-649", "649", "sinh-hoc-MOI-de-16", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-sinh-hoc-12-e-so-17-650", "650", "sinh-hoc-MOI-de-17", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-sinh-hoc-12-e-so-18-651", "651", "sinh-hoc-MOI-de-18", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-sinh-hoc-12-e-so-19-652", "652", "sinh-hoc-MOI-de-19", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-sinh-hoc-12-e-so-20-653", "653", "sinh-hoc-MOI-de-20", [40,50])

# dia ly MOI
giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-ia-li-12-e-so-01-656", "656", "dia-ly-MOI-de-01", [30,40])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-ia-li-12-e-so-02-657", "657", "dia-ly-MOI-de-02", [40,50])
# broken link
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-ia-li-12-e-so-03-658", "658", "dia-ly-MOI-de-03", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-ia-li-12-e-so-04-659", "659", "dia-ly-MOI-de-04", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-ia-li-12-e-so-05-660", "660", "dia-ly-MOI-de-05", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-ia-li-12-e-so-06-661", "661", "dia-ly-MOI-de-06", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-ia-li-12-e-so-07-662", "662", "dia-ly-MOI-de-07", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-ia-li-12-e-so-08-663", "663", "dia-ly-MOI-de-08", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-ia-li-12-e-so-09-664", "664", "dia-ly-MOI-de-09", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-ia-li-12-e-so-10-665", "665", "dia-ly-MOI-de-10", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-ia-li-12-e-so-11-666", "666", "dia-ly-MOI-de-11", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-ia-li-12-e-so-12-667", "667", "dia-ly-MOI-de-12", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-ia-li-12-e-so-13-668", "668", "dia-ly-MOI-de-13", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-ia-li-12-e-so-14-669", "669", "dia-ly-MOI-de-14", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-ia-li-12-e-so-15-670", "670", "dia-ly-MOI-de-15", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-ia-li-12-e-so-16-671", "671", "dia-ly-MOI-de-16", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-ia-li-12-e-so-17-672", "672", "dia-ly-MOI-de-17", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-ia-li-12-e-so-18-673", "674", "dia-ly-MOI-de-18", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-ia-li-12-e-so-19-674", "674", "dia-ly-MOI-de-19", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-ia-li-12-e-so-20-675", "675", "dia-ly-MOI-de-20", [40,50])


# toan hoc MOI
giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-toan-12-e-so-01-586", "586", "toan-hoc-MOI-de-01", [30,40])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-toan-12-e-so-02-587", "587", "toan-hoc-MOI-de-02", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-toan-12-e-so-03-588", "588", "toan-hoc-MOI-de-03", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-toan-12-e-so-04-589", "589", "toan-hoc-MOI-de-04", [40,50])
# broken link
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-toan-12-e-so-05-590", "590", "toan-hoc-MOI-de-05", [40,50])

# broken link
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-toan-12-e-so-06-591", "591", "toan-hoc-MOI-de-06", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-toan-12-e-so-07-592", "592", "toan-hoc-MOI-de-07", [40,50])
# giai_de("http://study.hanoi.edu.vn/ky-thi/on-thpt-mon-toan-12-e-so-08-593", "593", "toan-hoc-MOI-de-08", [40,50])












