# SejongSQL
**2022년 1학기 세종대학교 창의학기제 - SQL Online Judge**

<img width="1719" alt="image" src="https://user-images.githubusercontent.com/29897277/186642627-9446e1c7-52b6-4b94-8219-c9a13eb813fb.png">

현재 세종대학교에는 각종 Programming 언어를 연습하는 Online Judge System이 존재하는 반면, SQL에 대한 Online Judge는 존재하지 않습니다. 본 프로젝트는 세종대학교 학생들이 쉽게 SQL을 학습할 수 있도록 Web 기반의 Judge System을 제공하여 언제 어디서나 SQL 연습 및 실습을 할 수 있는 학습 환경을 제공할 수 있는 것을 목표로 합니다.


## SejongSQL의 특징

- 인터넷이 연결된다면 언제 어디서나 연습 가능
- 가상 DB을 통해 언제 어디서 안전하게 쿼리 테스트 가능
- 자신이 작성한 쿼리에 대한 성능 분석 기능 지원
- 수업 모드 / 시험 모드 등, 학교 강의에 최적화된 기능 지원

### Web기반 데이터베이스 실습 환경 제공

<img width="994" alt="image" src="https://user-images.githubusercontent.com/29897277/186644135-359ca078-9bc7-40a6-a5d1-64b63cc11243.png">

SSQL은 인터넷 환경이 보장된다면 언제 어디서든 SQL Query 실습이 가능합니다. 기존에는 교수 및 조교와 같은, 분반 관리자가 학생들에게 일일히 실습 데이터를 배포하여 학생들이 직접 각각의 PC에 SQL 데이터를 포함한 모든 실습 환경을 구축해야만 했습니다.

하지만, SSQL은 분반 관리자가 한번 만 클라우드 상에 실습 데이터를 업로드하면, 이후 분반에 속한 모든 사용자가 해당 실습 데이터에 접근하여 해당 환경에서 자유롭게 학습을 수행할 수 있습니다!

### 쿼리 효율성 분석 기능

<img width="715" alt="image" src="https://user-images.githubusercontent.com/29897277/186645164-bd1971fd-672f-4fd0-b6e6-1eccecbaa9be.png">

기존의 수업 진행 방식에서는, 학생들이 제출한 Query문에 대하여 단순히 정답 불/일치 체크만 진행하였습니다.

하지만 SSQL에서는 이러한 쿼리에서 도출된 결과의 매칭 결과 뿐만 아니라 더 나아가 해당 Query의 효율성 측면도 검증합니다.여기서 말하는 효율성이란, **Full table / Index Scan, File Sort, Uncacheable** 등 다양하며 이는 **관리자가 문제마다 원하는 조건을 지정**할 수 있게 구현되어 있습니다. 

이를 통해 사용자는 쿼리의 정답 여부 뿐 아니라 보다 좋은 쿼리를 작성하기 위한 개선 방향성을 제시 받을 수 있습니다.

### 대학 강의를 위한 올인원 플랫폼

<img width="1001" alt="image" src="https://user-images.githubusercontent.com/29897277/186811003-8ee556da-c412-4ba6-a5df-8c838a0eaca5.png">

저희들은 SSQL를 만들기 위해 기존 DB 관련 강의 커리큘럼을 면밀히 분석하고, 학생들과 교수/조교님들에게 더욱 편리하게 강의가 다가올 수 있도록 지속적인 피드백을 통해 서비스를 개선하였습니다. 

- Excel 등의 외부 툴에 의존하지 않고 학생들의 성적 관리 지표 및 통계 인터페이스 제공
- 학생들이 제출한 Query문에 대한 분석/실행 결과를 교수/조교가 함께 확인 및 개인별 원격 피드백 기능
- 가상 DB를 통해 문제별 환격 격리 및 시험 모드 제공
- Query의 효율성 분석을 포함한 모든 문제의 채점 자동화 지원




## 서비스 구성도

