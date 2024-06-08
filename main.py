from i3ipc import Connection, Event
import logging


# Encapsulate workspace's old values
class OldValues:
    def __init__(self, name, num):
        self.name = name
        self.num = num


# Make bold name using pango markup
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
    # Use workspace number as new name if workspace is emptied (last window on workspace is closed)
    rename_ws(i3,
              OldValues(current_ws.name, current_ws.num),
              current_ws.num)


def on_window_new(i3, e):
    win = e.container
    current_ws = find_ws_by_id(i3, win.id)
    # Rename workspace to new window's class even if not focused
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
        # Use workspace number as new name if window's class is unspecified
        if win.window_class is not None:
            rename_ws(i3,
                      OldValues(current_ws.name, current_ws.num),
                      make_ws_name(current_ws.num, win.window_class))
        else:
            rename_ws(i3,
                      OldValues(current_ws.name, current_ws.num),
                      current_ws.num)


# Use a window's id to find its containing workspace
def find_ws_by_id(i3, id):
    # Unfortunately, the i3 ipc protocol doesn't allow finding a container's parent directly,
    # hence this iterative approach
    for output in i3.get_tree().root().nodes:
        if output.find_by_id(id) is not None:
            content = output.nodes[1]
            for ws in content.nodes:
                if ws.find_by_id(id) is not None:
                    logging.debug(f'found window {id} on workspace {ws.name}')
                    return ws
    logging.debug(f'failed to find window {id}')
    return None


# Find the workspace of the currently focused window
def find_focused_ws(i3):
    # Same approach as find_ws_by_id function
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
    # Rename focused workspace on script launch
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
