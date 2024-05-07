import flair
import flair_render as fr

import rec.renderSettings


def main() -> None:
    rec.renderSettings.setGlobals()
    rec.renderSettings.setFlair()

    flair.check()

    renderer = fr.Renderer(alpha="Premult.", img_format=".png", taa=True)  # type: ignore
    renderer.set_folders(scene_folder=False)
    renderer.render()


main()
