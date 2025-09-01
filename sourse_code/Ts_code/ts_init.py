import sys
def init_env(path):
    tool_path = path + "/tools"
    infer_path = tool_path + "/infer"
    sys.path.insert(0, path)
    sys.path.insert(0, tool_path)
    sys.path.insert(0, infer_path)
