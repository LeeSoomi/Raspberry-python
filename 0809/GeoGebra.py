from google.colab import files
from PIL import Image
import matplotlib.pyplot as plt

# 이미지 파일 업로드
uploaded = files.upload()

# 이미지 열기
image = Image.open(list(uploaded.keys())[0])
plt.imshow(image)
plt.axis('off')
plt.show()
