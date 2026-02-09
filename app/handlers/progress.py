import requests
import json

# Конфигурация
API_URL = "https://api.newlxp.ru/graphql"
AUTH_DATA = {
    "email": "EsmurzievMM23@magas.ithub.ru",
    "password": "Buc85339"
}

def login():
    """Функция авторизации"""
    print('🔐 Отправка запроса авторизации...')
    
    auth_query = """
    query SignIn($input: SignInInput!) {
      signIn(input: $input) {
        user { id isLead __typename }
        accessToken
        __typename
      }
    }"""

    try:
        response = requests.post(API_URL, json={
            "operationName": "SignIn",
            "query": auth_query,
            "variables": {
                "input": AUTH_DATA
            }
        }, headers={
            "Content-Type": "application/json",
            "apollographql-client-name": "web"
        })
        
        response.raise_for_status()
        data = response.json()
        
        print('✅ Авторизация успешна')
        return data['data']['signIn']
        
    except Exception as e:
        print(f'❌ Ошибка авторизации: {e}')
        if hasattr(e, 'response') and e.response:
            print(f'Ответ сервера: {e.response.text}')
        exit(1)

def get_diary(token, student_id):
    """Функция получения дневника"""
    print('\n📖 Загрузка данных дневника...')

    diary_query = """
    query DiaryQuery($studentId: UUID!) {
      searchStudentDisciplines(input: { studentId: $studentId }) {
        discipline {
          name
          code
          teachers {
            user {
              lastName
              firstName
              middleName
            }
          }
        }
        disciplineGrade
        maxScoreForAnsweredTasks
        scoreForAnsweredTasks
        disciplineAttendance {
          percent
          total
          visited
        }
      }
    }"""

    try:
        response = requests.post(API_URL, json={
            "operationName": "DiaryQuery",
            "query": diary_query,
            "variables": {"studentId": student_id}
        }, headers={
            "Content-Type": "application/json",
            "apollographql-client-name": "web",
            "authorization": f"Bearer {token}"
        })
        
        response.raise_for_status()
        data = response.json()
        
        return data['data']['searchStudentDisciplines']
        
    except Exception as e:
        print(f'❌ Ошибка загрузки дневника: {e}')
        if hasattr(e, 'response') and e.response:
            print(f'Ответ сервера: {e.response.text}')
        exit(1)

def format_teachers(teachers):
    """Форматирование списка преподавателей"""
    formatted = []
    for teacher in teachers:
        user = teacher['user']
        name = f"{user['lastName']} {user['firstName']} {user['middleName']}"
        formatted.append(name)
    return ', '.join(formatted)

def main():
    """Главный процесс"""
    # Авторизация
    auth_result = login()
    token = auth_result['accessToken']
    user = auth_result['user']
    print(f'👤 Студент ID: {user["id"]}')

    # Получение дневника
    diary = get_diary(token, user['id'])
    
    # Сохранение полных данных
    with open('diary_full.json', 'w', encoding='utf-8') as f:
        json.dump(diary, f, ensure_ascii=False, indent=2)
    
    # Красивый вывод
    print('\n=== УСПЕВАЕМОСТЬ ===\n')
    
    for item in diary:
        discipline = item['discipline']
        attendance = item['disciplineAttendance']
        
        print(f"📚 {discipline['name']} ({discipline['code']})")
        print(f"👨‍🏫 Преподаватели: {format_teachers(discipline['teachers'])}")
        print(f"⭐ Оценка: {item['disciplineGrade'] or 'нет'} "
              f"({item['scoreForAnsweredTasks']}/{item['maxScoreForAnsweredTasks']} баллов)")
        print(f"📊 Посещаемость: {attendance['visited']}/{attendance['total']} "
              f"({attendance['percent']}%)")
        print('-' * 35)
    
    print(f'\n💾 Полные данные сохранены в diary_full.json')

if __name__ == "__main__":
    main()