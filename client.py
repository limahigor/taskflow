import argparse
import json
import requests

BASE_URL = "http://127.0.0.1:8000"

STATUS_MAP = {
    0: "pendent",
    1: "on going",
    2: "completed"
}

def create_user(name, email):
    """ Create a new user """
    data = {"name": name, "email": email}
    response = requests.post(f"{BASE_URL}/users/", json=data)
    format_single_response(response, "User created")

def list_users():
    """ List all users """
    response = requests.get(f"{BASE_URL}/users/")
    format_list_response(response, "Users", ["id", "name", "email"])

def create_task(title, description, user_id):
    """ Create a new task """
    data = {"title": title, "description": description, "user_id": user_id}
    response = requests.post(f"{BASE_URL}/tasks/", json=data)
    format_single_response(response, "Task created")

def update_task_status(task_id, status_code):
    """ Update the status of a task """
    if status_code not in STATUS_MAP:
        print("Error: Invalid status code. Use 0 (pendent), 1 (on going), or 2 (completed).")
        return
    
    data = {"status": status_code}
    response = requests.put(f"{BASE_URL}/tasks/{task_id}", json=data)
    format_single_response(response, "Task updated")

def list_tasks():
    """ List all tasks """
    response = requests.get(f"{BASE_URL}/tasks/")
    format_list_response(response, "Tasks", ["id", "title", "description", "status", "user"])

def save_tasks_to_json(filename="tasks.json"):
    """ Save all tasks to a JSON file """
    response = requests.get(f"{BASE_URL}/tasks/")
    if response.status_code == 200:
        tasks = response.json()
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(tasks, file, indent=4)
        print(f"Tasks saved to {filename}")
    else:
        print("Error: Unable to retrieve tasks")
        format_single_response(response, "Error")

def format_single_response(response, header):
    """ Format a single response (User created, Task created, Task updated) """
    print(f"\n=============== {header} ===============")
    if response.status_code == 200:
        data = response.json()
        for key, value in data.items():
            if isinstance(value, dict):
                print(f"{key.capitalize()}:")
                for sub_key, sub_value in value.items():
                    print(f"  {sub_key.capitalize()}: {sub_value}")
            else:
                print(f"{key.capitalize()}: {value}")
    else:
        error_data = response.json()
        print(f"Error: {error_data.get('detail', 'Unknown error')}")
    print("=====================================\n")

def format_list_response(response, header, keys):
    """ Format a list response (List users, List tasks) """
    print(f"\n=============== {header} ===============")
    if response.status_code == 200:
        data = response.json()
        for item in data:
            print("-------------------------------------")
            for key in keys:
                if key == "user" and isinstance(item[key], dict):
                    print(f"User:")
                    print(f"  Id: {item[key]['id']}")
                    print(f"  Name: {item[key]['name']}")
                    print(f"  Email: {item[key]['email']}")
                else:
                    print(f"{key.capitalize()}: {item[key]}")
    else:
        error_data = response.json()
        print(f"Error: {error_data.get('detail', 'Unknown error')}")
    print("=====================================\n")

def main():
    parser = argparse.ArgumentParser(description="CLI client for managing users and tasks in FastAPI")
    subparsers = parser.add_subparsers(dest="command")

    user_parser = subparsers.add_parser("create-user", help="Create a new user")
    user_parser.add_argument("name", type=str, help="User name")
    user_parser.add_argument("email", type=str, help="User email")

    subparsers.add_parser("list-users", help="List all users")

    task_parser = subparsers.add_parser("create-task", help="Create a new task")
    task_parser.add_argument("title", type=str, help="Task title")
    task_parser.add_argument("description", type=str, help="Task description")
    task_parser.add_argument("user_id", type=int, help="ID of the user assigned to the task")

    update_task_parser = subparsers.add_parser("update-task", help="Update the status of a task")
    update_task_parser.add_argument("task_id", type=int, help="Task ID")
    update_task_parser.add_argument("status_code", type=int, choices=[0, 1, 2], help="Status code (0: pendent, 1: on going, 2: completed)")

    subparsers.add_parser("list-tasks", help="List all tasks")

    save_parser = subparsers.add_parser("save-tasks", help="Save tasks to a JSON file")
    save_parser.add_argument("--filename", type=str, default="tasks.json", help="Output file name (default: tasks.json)")

    args = parser.parse_args()

    if args.command == "create-user":
        create_user(args.name, args.email)
    elif args.command == "list-users":
        list_users()
    elif args.command == "create-task":
        create_task(args.title, args.description, args.user_id)
    elif args.command == "update-task":
        update_task_status(args.task_id, args.status_code)
    elif args.command == "list-tasks":
        list_tasks()
    elif args.command == "save-tasks":
        save_tasks_to_json(args.filename)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()