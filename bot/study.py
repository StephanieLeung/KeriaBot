import asyncio
from typing import Optional

import discord
from discord.ext import commands
from discord.ui import View, Button, TextInput, Modal

from helpers.restrictUsers import restricted_users
from helpers.todoItem import TodoItem, display_todo_embed, check_buttons
from helpers.cookieFuncs import update_cookies

todo_threads = {}


class ItemForm(Modal, title="Add Item to Todo"):
    text_input = TextInput(label="Item to add", style=discord.TextStyle.short,
                           placeholder="Todo here...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        todo_threads[interaction.channel.id].add(self.text_input.value)
        await interaction.response.send_message("Added!", ephemeral=True, delete_after=1)
        await display_todo_embed(todo_threads[interaction.channel.id])


async def create_embed(user: discord.User, thread: discord.Thread, todo_item: Optional[TodoItem] = None) -> TodoItem:
    todo_embed = discord.Embed(
        title="Study Session (beta)",
        description="Click the 'Add Item' button to add to your to-do list. Use `!rm` to remove from the list by name "
                    "or number.",
    )
    todo_embed.add_field(name="To-do List", value="")
    todo_view = View()

    next_button = Button(label="Next", style=discord.ButtonStyle.blurple)
    back_button = Button(label="Back", style=discord.ButtonStyle.grey)
    add_item = Button(label="Add Item", style=discord.ButtonStyle.green)
    todo_view.add_item(back_button)
    todo_view.add_item(next_button)
    todo_view.add_item(add_item)

    if todo_item is None:
        todo_msg = await thread.send(embed=todo_embed)
        todo_item = TodoItem(embed=todo_embed, view=todo_view, message=todo_msg, user=user)
        todo_threads[thread.id] = todo_item
        back_button.disabled = True
        next_button.disabled = True
    else:
        todo_item.update(embed=todo_embed, view=todo_view)

    todo = todo_item.get_todo()

    async def next_button_callback(interaction: discord.Interaction):
        todo_item.next_page()
        await display_todo_embed(todo_item)
        if len(todo) - ((todo_item.page - 1) * 5) <= 5:
            next_button.disabled = True
        back_button.disabled = False
        await interaction.response.edit_message(embed=todo_item.get_embed(), view=todo_view)

    async def back_button_callback(interaction: discord.Interaction):
        todo_item.back_page()
        await display_todo_embed(todo_item)
        if todo_item.page == 1:
            back_button.disabled = True
        next_button.disabled = False
        await interaction.response.edit_message(embed=todo_item.get_embed(), view=todo_view)

    async def add_item_callback(interaction: discord.Interaction):
        if interaction.user == todo_item.user:
            await interaction.response.send_modal(ItemForm())
            await display_todo_embed(todo_item)
        else:
            await interaction.response.send_message("You must be the owner of this to-do list to add to it.",
                                                    ephemeral=True)

    next_button.callback = next_button_callback
    back_button.callback = back_button_callback
    add_item.callback = add_item_callback

    return todo_item


class Study(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def study_timer(self, ctx, minutes: int, thread: discord.Thread):
        todo_item = await create_embed(ctx.author, thread)
        await display_todo_embed(todo_item)

        timer_embed = discord.Embed(title="Pomodoro Timer")
        timer_embed.add_field(name="Timer", value=str(minutes) + " minutes remaining.")
        timer_msg = await thread.send(embed=timer_embed)

        async def update_todo():
            def check(m):
                return m.channel.id == thread.id and m.author == ctx.author

            while True:
                try:
                    await self.bot.fetch_channel(thread.id)
                    message = await self.bot.wait_for('message', check=check)
                    if message.content.lower() == "end":
                        todo_threads.pop(thread.id)
                        await thread.delete()
                        break
                    elif message.content.startswith('!rm'):
                        content = message.content[4:]
                        try:
                            todo_item.remove(content)
                            await display_todo_embed(todo_item)
                        except ValueError:
                            await thread.send("value error")
                        except IndexError:
                            await thread.send("index error")

                    await thread.delete_messages([message])
                except asyncio.TimeoutError:
                    continue

        async def timer(value):
            update_embed = value / 60
            try:
                while value != 0:
                    await asyncio.sleep(1)
                    value -= 1
                    mins = value // 60
                    sec = value % 60
                    timer_embed.set_field_at(0,
                                             name="Timer",
                                             value=str(mins) + ":" + "{:02}".format(sec) + " minutes remaining.")
                    await timer_msg.edit(embed=timer_embed)
                    if sec == 0 and mins == update_embed - 3:
                        await create_embed(ctx.author, thread, todo_item)
                        await display_todo_embed(todo_item)
                        update_embed -= 3
            except discord.NotFound:
                return

        sessions = 0
        while True:
            try:
                todo_task = asyncio.create_task(update_todo())
                timer_task = asyncio.create_task(timer(minutes * 60))
                await timer_task
                await thread.send(ctx.author.mention +
                                  ". Starting break timer for 5 minutes. Feel free to keep updating your todo list! "
                                  "You can now use commands.")
                sessions += 1
                break_task = asyncio.create_task(timer(5 * 60))
                restricted_users.remove_user(ctx.author.id)
                await break_task
                todo_task.cancel()
                await thread.delete_messages([message async for message in thread.history(limit=1)])
                await thread.send(ctx.author.mention +
                                  " Restarting your pomodoro timer!")
                restricted_users.add_user(ctx.author.id)
            except discord.NotFound:
                restricted_users.remove_user(ctx.author.id)
                break

        return sessions

    @commands.hybrid_command(name="pomodoro", aliases=['pomo'])
    async def pomodoro(self, ctx, minutes: int):
        restricted_users.add_user(ctx.author.id)

        thread = await ctx.channel.create_thread(
            name=ctx.message.author.display_name + "'s Study Session",
            auto_archive_duration=24*60,
            type=discord.ChannelType.private_thread
        )

        await thread.add_user(ctx.author)
        await thread.send("Your pomodoro timer has been started! Type `end` to stop this session. Note that you won't "
                          "be able to use any commands while your study session is active.")
        await thread.edit(slowmode_delay=2)
        await ctx.send("**" + ctx.message.author.display_name + "'s Study Session** was created: \n" + thread.mention)
        sessions = await self.study_timer(ctx, minutes, thread)
        add = minutes * sessions * 8
        cookies = update_cookies(ctx.guild.id, ctx.author.id, add)
        await ctx.send(ctx.author.mention + f". `{sessions}` study session(s) completed. You earned **{add}** cookies. "
                                            f"You now have **{cookies}** cookies in your bank.")


async def setup(bot):
    await bot.add_cog(Study(bot))
