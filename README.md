# CollectRaptor

`CollectRaptor` is a simple Python command-line utility to automatically
generate a [`Velociraptor`](https://github.com/Velocidex/velociraptor)
standalone binary to collect forensic artifacts.

### Description

`CollectRaptor` currently supports the following target operating systems and
collection profiles:

  - `Windows` (x86 / x64) with `Velociraptor` built-in
    `Windows.KapeFiles.Targets` artifact.

    Template files:
      - [`Windows_collector_KAPE_light.template`](./templates/Windows_collector_KAPE_light.template)
      - [`Windows_collector_KAPE_full.template`](./templates/Windows_collector_KAPE_full.template)


  - `Linux` (x64) with artifact definitions retrieved from the
    [ForensicArtifacts's artifacts](https://github.com/ForensicArtifacts/artifacts)
    repository and collected with the `Linux.Search.FileFinder` artifact.

    Template file:
      - [`Linux_collector.template`](./templates/Linux_collector.template)

### Usage

###### Quick usage

```
CollectRaptor [-h] [-t TEMPLATE] [-o OUTPUT] [--only-conf ONLY_CONF] [--velo-path VELO_PATH] {Windows,Linux}
```

###### Windows collector

```
CollectRaptor Windows [-h] [-a {x86,x64}] {kape_light,kape_full} ...

positional arguments:
  {kape_light,kape_full}

common arguments:
    -h, --help            show this help message and exit
    -t TEMPLATE, --template TEMPLATE
                          Template file to parametrize
    -o OUTPUT, --output OUTPUT
                          Output directory for the config file and packed Velociraptor binary
    --only-conf ONLY_CONF
                          Only generate a config file, not the packed Velociraptor binary
    --velo-path VELO_PATH
                          Path to a folder containing the Velociraptor binaries to use for packing the collector

Windows arguments:
  -h, --help            show this help message and exit
  -a {x86,x64}, --architecture {x86,x64}
                        Target operating system architecture
```

###### Linux collector

```
CollectRaptor Linux [-h] [-a {x64}] {forensic_artifacts}

positional arguments:
  {forensic_artifacts}

common arguments:
    -h, --help            show this help message and exit
    -t TEMPLATE, --template TEMPLATE
                          Template file to parametrize
    -o OUTPUT, --output OUTPUT
                          Output directory for the config file and packed Velociraptor binary
    --only-conf ONLY_CONF
                          Only generate a config file, not the packed Velociraptor binary
    --velo-path VELO_PATH
                          Path to a folder containing the Velociraptor binaries to use for packing the collector

forensic_artifacts options:
  -u YAML_URLS [YAML_URLS ...], --url YAML_URLS [YAML_URLS ...]
                        One or more URL(s) to retrieve YAML files from
  -f YAML_FILES [YAML_FILES ...], --file YAML_FILES [YAML_FILES ...]
                        One or more artifacts YAML file(s)
```

### Acknowledgements

Thanks to [koromodako](https://github.com/koromodako)
(from [`CERT-EDF`](https://twitter.com/Cert_EDF)) for the idea on the Linux
collector!

### Authors

[Thomas DIOT (Qazeer)](https://github.com/Qazeer/)

### Licence

CC BY 4.0 licence - https://creativecommons.org/licenses/by/4.0/
