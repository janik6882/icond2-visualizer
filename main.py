import io
import matplotlib.pyplot as plt
import numpy as np
import requests
import xarray as xr
from mpl_toolkits.basemap import Basemap
import bz2
from datetime import datetime, timedelta


def get_links(base_url):
    r = requests.get(base_url)
    links = []
    for link in r.text.split("\n"):
        if "href" in link:
            links.append(link.split("href=")[1].split(">")[0].replace('"', ""))
    return links


def get_data(url):
    r = requests.get(url)
    zipped_file = io.BytesIO(r.content)
    unzipped_file = bz2.decompress(zipped_file.read())
    with open("data/temp.grib2", "wb") as f:
        f.write(unzipped_file)
    return xr.open_dataset("data/temp.grib2", engine="cfgrib").get("tp")


def create_image(ds, name):
    plt.style.use("dark_background")
    ax, fig = plt.subplots(figsize=(30, 30))
    filename = name[45:45+14]
    timestamp = filename[:-4]
    time_delta = int(filename[-3:])
    timestamp_start = datetime.strptime(timestamp, "%Y%m%d%H")
    timestamp_end = timestamp_start + timedelta(hours=time_delta)
    title = f"Total precipitation from {timestamp_start} to {timestamp_end} (for {time_delta} hours)"
    plt.title(title)
    dwd_link_source = "https://opendata.dwd.de/weather/nwp/icon-d2/grib/12/tot_prec/"
    plt.text(0.5, 0.5, f"Source: DWD Open Data server, ICON D2 Model \nLink: {dwd_link_source}\nCopyright: Janik Klauenberg")
    if "step" in ds.indexes:
        ds = ds.sel(step=ds.indexes["step"].min())
    ds = ds.sel(latitude=slice(47, 56), longitude=slice(6, 15))
    min_lon = 6
    max_lon = 15
    min_lat = 47
    max_lat = 56
    m = Basemap(projection="merc", llcrnrlat=min_lat, urcrnrlat=max_lat, llcrnrlon=min_lon, urcrnrlon=max_lon, resolution="h")
    X = np.linspace(0, m.urcrnrx, ds.shape[0])
    Y = np.linspace(0, m.urcrnry, ds.shape[1])
    xx, yy = np.meshgrid(X, Y)
    m.drawcountries(linewidth=1.25, color="#ffffff")
    m.fillcontinents(color='#232323')
    cs = plt.contourf(xx, yy, ds, cmap="viridis_r", alpha=0.5, zorder=3,  extend="max", levels=np.arange(1, 60, 7), vmin=1, vmax=50)
    cs.cmap.set_over("red")
    m.readshapefile("ressources\DEU_adm1", "DEU_adm1", color="#ffffff")
    plt.colorbar()
    plt.axis("off")
    output_name = f"{timestamp_start.strftime('%Y%m%d%H')}_{timestamp_end.strftime('%Y%m%d%H')}"
    plt.savefig(f"images/{output_name}.png", transparent=True, bbox_inches="tight", pad_inches=0, dpi=300, facecolor="#232323")


if __name__ == '__main__':

    base = "https://opendata.dwd.de/weather/nwp/icon-d2/grib/12/tot_prec/"
    links = get_links(base)[50]
    links = [links[6], links[12], links[24], links[48]]
    for link in links:
        print(link)
        url = base + link
        x = get_data(url)
        create_image(x, link)
