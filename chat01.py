# '''chapter08_CA.chatbot.py v1.0'''

# human_name = input('당신의 이름:')
# bot_name = 'AI'

# qna_dict = {
# "안녕" : "안녕 하세요. ^^",
# "이름" : "제 이름은 AI 입니다.",
# "기분" : "저도 기분이 좋아요~!",
# "음악" : "저는 방탄소년단이 좋아요."
# }


# while True:
#     talk = input("%s : " %human_name)
#     for qna in qna_dict:
#         if qna in talk:
#             print("%s : %s\n" %(bot_name, qna_dict[qna]))
#             break
#     if qna not in talk:
#         print('죄송해요. 답변을 준비하도록 할께요.\n')
#         continue



import random

human_name = input('당신의 이름:')
bot_name = 'AI'

qna_dict = {
"안녕": "안녕 하세요. ^^",
"이름": "제 이름은 AI 입니다.",
"기분": "저도 기분이 좋아요~!",
"음악": ["저는 방탄소년단이 좋아요.", "저는 블랙핑크도 좋아해요!", "저는 클래식 음악을 자주 들어요."]
}

while True:
    talk = input("%s : " % human_name)
    for qna in qna_dict:
        if qna in talk:
            if qna == "음악":
                # 음악에 대한 답변을 랜덤하게 선택
                print("%s : %s\n" % (bot_name, random.choice(qna_dict[qna])))
            else:
                print("%s : %s\n" % (bot_name, qna_dict[qna]))
            break
    else:
        print('죄송해요. 답변을 준비하도록 할께요.\n')
        continue
