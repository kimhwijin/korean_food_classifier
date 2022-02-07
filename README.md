 # korean_food_classifier


![image](https://user-images.githubusercontent.com/33340741/152799667-1145bd0c-23b9-4461-9248-379079d8f119.png)
![image](https://user-images.githubusercontent.com/33340741/152803530-02949121-2f13-4ecc-9d0a-7565a6e975e1.png)

[한국음식이미지 데이터](https://aihub.or.kr/aidata/13594)를 이용한 이미지 분류기 모델

## 데이터셋 정보
범주 : 총 150 개의 음식종류 [Label, Class](https://github.com/kimhwijin/korean_food_classifier/blob/master/class_to_label.txt) 

이미지 : png, jpg, jpeg, gif, bmp 형식의 다양한 이미지
- 각 범주당 1000개의 이미지, 총 15만개의 이미지가 포함된다.

구조 :

```
압축 해제 전

-kfood.zip
--class1.zip
--...

후

-kfood
--class1
---subclass1
----crop_area.properties
----Img_000_0000.jpg
----...
---...
--...

```

## Dataset

tf.data.Dataset 을 이용한 데이터 파이프라인 구축 : [kfood_dataset.py](https://github.com/kimhwijin/korean_food_classifier/blob/master/kfood_dataset.py)

### 대용량 데이터를 훈련하기 위한 데이터 전처리 방식
1. 모든 데이터의 경로들을 모아 데이터셋으로 생성한다.
2. 데이터경로를 통해 이미지를 로드한다.
3. 이미지 전처리를 수행하고 레이블을 지정한다.
4. shuffle, batch, repeat, prefetch 을 지정한다.

### 이미지 전처리 구성
1. 한국음식 데이터에 포함되어있는 crop_area.properties 의 크롭 정보를 통해 이미지를 자른다.
2. Random Crop : 이미지를 랜덤하게 90% 축소시키면서 자른다.
3. Central Crop : 이미지의 너비와 높이가 동일하도록 중앙을 기준으로 자른다.
4. 위의 Crop 중 한가지를 수행후, 이미지 사이즈 299x299 가 되도록 Resize 한다.
5. 이미지 픽셀 값이 0 ~ 1 이 되도록 float32 로 변환후 정규화 한다.
6. 레이블은 One-Hot Encoding 을 수행한다.


## Model

|모델 이름|구조|파라미터|훈련 에폭|정확도|
|---|---|---|---|---|
|KerasInceptionResNetV2|[Structure](https://github.com/kimhwijin/korean_food_classifier/blob/master/application/KerasInceptionResNetV2)|54,567k|20|20%|
|CustomInceptionResNetV2|[Structure](https://github.com/kimhwijin/korean_food_classifier/blob/master/application/inception_resnet_v2.py)|54,567k|40|93%|
|CustonInceptionResNetV2 + SEBlock|[Structure](https://github.com/kimhwijin/korean_food_classifier/blob/master/application/inception_resnet_v2_se.py)|62,923k|40|67%|


