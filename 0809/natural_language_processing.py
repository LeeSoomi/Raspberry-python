# !pip install nltk

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# NLTK 데이터 다운로드
nltk.download('punkt')
nltk.download('stopwords')

# 예제 문장
sentence = "Natural Language Processing with Python is an amazing experience."

# 단어 토큰화
words = word_tokenize(sentence)

# 불용어 제거
stop_words = set(stopwords.words('english'))
filtered_words = [word for word in words if word.lower() not in stop_words]

print("Tokenized Words:", words)
print("Filtered Words:", filtered_words)
