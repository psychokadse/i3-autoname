from i3ipc import Connection, Event
import logging


class OldValues:
    def __init__(self, name, num):
        self.name = name
        self.num = num


def make_ws_name(ws_num, ws_name):
    return f'{ws_num}:<b>{ws_name}</b>'


def rename_ws(i3, old_values, new_name):
    if old_values.name != new_name:
        i3.command(f'rename workspace {old_values.name} to {new_name}')
        logging.debug(f'renamed workspace number {old_values.num} to {new_name}')


def on_workspace_focus(i3, e):
    current_ws = e.current
    logging.debug(f'workspace {current_ws.name} focused')


def on_window_focus(i3, e):
    current_ws = find_focused_ws(i3)
    win = e.container
    logging.debug(f'window {win.window_title} focused')
    if current_ws is not None:
        rename_ws(i3,
                  OldValues(current_ws.name, current_ws.num),
                  make_ws_name(current_ws.num, win.window_class))


# This doesn't work because the container that is searched for doesn't exist anymore.
# def on_window_close(i3, e):
#     win = e.container
#     closed_ws = find_ws_by_id(i3, win.id)
#     logging.debug(f'window {win.window_title} closed')
#     if closed_ws is not None:
#         match len(closed_ws.nodes):
#             case 0:
#                 rename_ws(i3,
#                           OldValues(closed_ws.name, closed_ws.num),
#                           closed_ws.num)
#             case 1:
#                 win = closed_ws.nodes[0]
#                 rename_ws(i3,
#                           OldValues(closed_ws.name, closed_ws.num),
#                           make_ws_name(closed_ws.num, win.window_class))

def on_workspace_empty(i3, e):
    current_ws = e.current
    logging.debug(f'workspace {current_ws.name} emptied')
    rename_ws(i3,
              OldValues(current_ws.name, current_ws.num),
              current_ws.num)


def on_window_new(i3, e):
    win = e.container
    current_ws = find_ws_by_id(i3, win.id)
    if current_ws is not None:
        logging.debug(f'new window {win.window_title} spawned')
        rename_ws(i3,
                  OldValues(current_ws.name, current_ws.num),
                  make_ws_name(current_ws.num, win.window_class))


def on_window_move(i3, e):
    win = e.container
    current_ws = find_ws_by_id(i3, win.id)
    if current_ws is not None:
        logging.debug(f'window {win.id} moved to workspace {current_ws.name}')
        rename_ws(i3,
                  OldValues(current_ws.name, current_ws.num),
                  make_ws_name(current_ws.num, win.window_class))


def find_ws_by_id(i3, id):
    for output in i3.get_tree().root().nodes:
        if output.find_by_id(id) is not None:
            content = output.nodes[1]
            for ws in content.nodes:
                if ws.find_by_id(id) is not None:
                    logging.debug(f'found window {id} on workspace {ws.name}')
                    return ws
    logging.debug(f'failed to find window {id}')
    return None


def find_focused_ws(i3):
    for output in i3.get_tree().root().nodes:
        if output.find_focused() is not None:
            content = output.nodes[1]
            for ws in content.nodes:
                if ws.find_focused() is not None:
                    logging.debug(f'found focused workspace {ws.name}')
                    return ws
    logging.debug('failed to find focused workspace: will be detected on workspace switch')
    return None


def main():
    i3 = Connection()
    current_ws = find_focused_ws(i3)
    if current_ws is not None:
        focused = current_ws.find_focused()
        if focused is not None:
            rename_ws(i3,
                      OldValues(current_ws.name, current_ws.num),
                      make_ws_name(current_ws.num, focused.window_class))
    i3.on(Event.WORKSPACE_FOCUS, on_workspace_focus)
    i3.on(Event.WINDOW_FOCUS, on_window_focus)
    # i3.on(Event.WINDOW_CLOSE, on_window_close)
    i3.on(Event.WINDOW_NEW, on_window_new)
    i3.on(Event.WINDOW_MOVE, on_window_move)
    i3.on(Event.WORKSPACE_EMPTY, on_workspace_empty)
    i3.main()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
