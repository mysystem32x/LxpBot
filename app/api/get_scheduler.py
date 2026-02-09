import requests
from db.models import User

from datetime import datetime, timedelta

query_get_me = """
query GetMe {
  getMe {
    id
    email
    firstName
    lastName
    roles
    isLead
    phoneNumber
    avatar
    createdAt
    updatedAt
    notificationsSettings {
      isPushDailyDigestOnEmail
      __typename
    }
    __typename
  }
}
"""

query_get_task = """

query StudentAvailableTasks($input: StudentAvailableTasksInput!) {
    studentAvailableTasks(input: $input) {
      hasMore
      page
      perPage
      total
      totalPages
      items {
        ...StudentAvailableTaskFragment
        __typename
      }
      __typename
      }
    }
    
    fragment StudentAvailableTaskFragment on StudentContentBlock {
      kind
      taskDeadline
      taskCanBeAnsweredAfterDeadline
      passDate
      testScore
      task {
        id
        scoreInPercent
        answers {
          id
          __typename
        }
        __typename
      }
      testInterval {
        from
        to
        __typename
      }
      customTaskDeadline {
        deadline
        formEducation {
          id
          startedAt
          finishedAt
          form
          studentId
          comment
          __typename
        }
        __typename
      }
      customTestInterval {
        interval {
          from
          to
          __typename
        }
        formEducation {
          id
          startedAt
          finishedAt
          form
          studentId
          comment
          __typename
        }
        __typename
      }
      studentTopic {
        status
        __typename
      }
      topic {
        name
        id
        isCheckPoint
        isForPortfolio
        chapterId
        chapter {
          id
          name
          disciplineId
          discipline {
            name
            code
            suborganization {
              organization {
                id
                name
                timezoneMinutesOffset
                __typename
              }
              __typename
            }
            __typename
          }
          __typename
        }
        __typename
      }
      contentBlock {
        ... on TaskDisciplineTopicContentBlock {
          id
          kind
          name
          maxScore
          __typename
        }
        ... on TestDisciplineTopicContentBlock {
          id
          name
          kind
          testMaxScore: maxScore
          canBePassed
          testId
          __typename
        }
        __typename
      }
      __typename
    }
"""

query_get_profile = """
query GetProfile {
  getProfile {
    id
    email
    firstName
    lastName
    phoneNumber
    avatar
    bio
    skills
    experience
    education
    createdAt
    updatedAt
    __typename
  }
}
"""

query_get_schedule = """
query ManyClassesForSchedule($input: ManyClassesInput!) {
  manyClasses(input: $input) {
    id
    from
    to
    name
    role
    isOnline
    isAutoMeetingLink
    meetingLink
    discipline {
      id
      name
      code
      __typename
    }
    learningGroup {
      id
      name
      __typename
    }
    classroom {
      id
      name
      __typename
    }
    teacher {
      id
      user {
        id
        firstName
        lastName
        __typename
      }
      __typename
    }
    __typename
  }
}
"""

def login(email, password):
    login_data = {
        "operationName": "SignIn",
        "query": "query SignIn($input: SignInInput!) { signIn(input: $input) { accessToken } }",
        "variables": {"input": {"email": email, "password": password}}
    }
    
    login_resp = requests.post("https://api.newlxp.ru/graphql", json=login_data)
    return login_resp.json()["data"]["signIn"]["accessToken"]

async def add_to_data(email, password, telegram_id):
    token = login(email, password)
    
    data = {
        "operationName": "GetMe",
        "query": query_get_me,
        "variables": {}
    }

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post("https://api.newlxp.ru/graphql", json=data, headers=headers)
    data = response.json()
    print(data)

    user = await User.get(telegram_id=telegram_id)
    user.update_from_dict({
        "phoneNumber": data["data"]["getMe"]["phoneNumber"],
        "firstName": data["data"]["getMe"]["firstName"],
        "lastName": data["data"]["getMe"]["lastName"],
        "avatar": data["data"]["getMe"]["avatar"] if data["data"]["getMe"]["avatar"] else "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQoup9xGtNGZa5i4NRTAgxr-urdEBQJZWYNcA&s",
        "role": data["data"]["getMe"]["roles"][0],
        "id_student": data['data']['getMe']['id'],
        "createdAt": data["data"]["getMe"]["createdAt"]
    })
    print(data['data']['getMe']['id'])
    await user.save()


async def get_tasks(email, password, telegram_id):
    # 1. Получаем пользователя
    user = await User.get_or_none(telegram_id=telegram_id)
    if not user:
        return None
    
    # 2. Логинимся (если функция login асинхронная - нужен await)
    token = login(email, password)  # или await login(...)
    
    # 3. Формируем GraphQL запрос
    data = {
        "query": query_get_task,  # используем заранее определенный query
        "variables": {
            "input": {
                "studentId": user.id_student,
                "pageSize": 10,  # лучше не 1, а больше
                "page": 1,
                "filters": {
                    "fromArchivedDiscipline": False
                }
            }
        },
        "operationName": "StudentAvailableTasks"  # добавляем имя операции
    }
    
    # 4. Отправляем запрос
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            "https://api.newlxp.ru/graphql",
            json=data,  # важно: json=, а не data=
            headers=headers
        )
        
        # 5. Проверяем ответ
        if response.status_code == 200:
            result = response.json()
            # GraphQL ошибки могут быть при 200 статусе!
            if "errors" in result:
                print(f"GraphQL ошибка: {result['errors']}")
                return None
            import pprint
            #pprint.pprint(result["data"]["studentAvailableTasks"])
            return result["data"]["studentAvailableTasks"]['items']
        else:
            print(f"HTTP ошибка: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Ошибка запроса: {e}")
        return None

async def get_profile(email, password):

    token = login(email, password)
    
    data = {
        "operationName": "GetProfile",
        "query": query_get_profile,
        "variables": {}
    }

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post("https://api.newlxp.ru/graphql", json=data, headers=headers)
    return response.json()
async def get_schedule(email, password):
    token = login(email, password)
    import pytz
    
        
    # Устанавливаем часовой пояс Москвы
    msk_tz = pytz.timezone('Europe/Moscow')

    # Получаем текущее время в Москве
    today_msk = datetime.now(msk_tz).isoformat()
    next_week_msk = (datetime.now(msk_tz) + timedelta(days=7)).isoformat()

    data = {
        "operationName": "ManyClassesForSchedule",
        "query": query_get_schedule,
        "variables": {
            "input": {
                "page": 1,
                "pageSize": 50,
                "filters": {
                    "interval": {  # ← ОБЯЗАТЕЛЬНОЕ ПОЛЕ
                        "from": today_msk,
                        "to": next_week_msk
                    }
                }
            }
        }
    }

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post("https://api.newlxp.ru/graphql", json=data, headers=headers)  # ← POST, а не GET
    return response.json()


async def get_task_details(token, topic_id, content_id, student_id):
    """Получает детали задания с описанием"""
    query = """
    query GetDisciplineTaskBlockByTopicIdAndContentId(
      $input: GetByTopicIdAndContentIdInput!
      $studentId: UUID!
    ) {
      getDisciplineTaskBlockByTopicIdAndContentId(input: $input) {
        id
        name
        maxScore
        body
        studentDeadline(studentId: $studentId)
        studentCanSendAnswers(studentId: $studentId)
        customStudentDeadline(studentId: $studentId) {
          deadline
        }
        __typename
      }
    }
    """
    
    variables = {
        "input": {
            "topicId": topic_id,
            "contentId": content_id
        },
        "studentId": student_id
    }
    
    data = {
        "query": query,
        "variables": variables,
        "operationName": "GetDisciplineTaskBlockByTopicIdAndContentId"
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            "https://api.newlxp.ru/graphql",
            json=data,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Проверка GraphQL ошибок
        if "errors" in result:
            print(f"GraphQL ошибка: {result['errors']}")
            return None
        
        # Возвращаем данные задания
        return result.get("data", {}).get("getDisciplineTaskBlockByTopicIdAndContentId")
        
    except Exception as e:
        print(f"Ошибка получения деталей задания: {e}")
        return None