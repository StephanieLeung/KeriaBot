import discord

class TodoItem:
    def __init__(self, embed: discord.Embed, view: discord.ui.View, message: discord.Message, user: discord.User):
        self.__embed = embed
        self.__view = view
        self.__message = message
        self.__todo = []
        self.page = 1
        self.user = user

    def add(self, todo: str):
        self.__todo.append(todo)

    def remove(self, todo: str):
        removed = False
        for item in self.__todo:
            if item.lower() == todo.lower():
                self.__todo.remove(item)
                removed = True
                break
        if removed:
            return
        else:
            try:
                index = int(todo)
                self.__todo.pop(index - 1)
            except Exception as e:
                raise e

    def update(self, embed: discord.Embed, view: discord.ui.View):
        self.__embed = embed
        self.__view = view

    def get_todo(self) -> list[str]:
        return self.__todo

    def get_embed(self) -> discord.Embed:
        return self.__embed

    def get_view(self) -> discord.ui.View:
        return self.__view

    def get_message(self) -> discord.Message:
        return self.__message

    def next_page(self):
        self.page += 1

    def back_page(self):
        self.page -= 1


async def display_todo_embed(todo_item: TodoItem):
    todo_str = ""
    todo = todo_item.get_todo()
    page = todo_item.page
    if len(todo) > 0:
        for i in range(min(len(todo) - (5 * (page - 1)), 5)):
            todo_str += f"{i + ((page - 1) * 5) + 1}. {todo[i + ((page - 1) * 5)]}\n"

    todo_item.get_embed().set_field_at(0, name="To-do List", value=todo_str)

    check_buttons(todo_item)
    await todo_item.get_message().edit(embed=todo_item.get_embed(), view=todo_item.get_view())


def check_buttons(todo_item: TodoItem):
    buttons = todo_item.get_view().children
    if len(todo_item.get_todo()) > todo_item.page * 5:
        buttons[1].disabled = False
    else:
        buttons[1].disabled = True

    if todo_item.page > 1:
        buttons[0].disabled = False
    else:
        buttons[0].disabled = True
