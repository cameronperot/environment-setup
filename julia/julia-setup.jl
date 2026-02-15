using Pkg

pkgs = [
    "BenchmarkTools",
    "CSV",
    "DataFrames",
    "DistributedArrays",
    "Distributions",
    "Documenter",
    "FFTW",
    "Flux",
    "HDF5",
    "IJulia",
    "ImageIO",
    "ImageMagick",
    "Images",
    "JLD",
    "JuliaFormatter",
    "LaTeXStrings",
    "LsqFit",
    "MKL",
    "NPZ",
    "OhMyREPL",
    "PackageCompiler",
    "Plots",
    "ProfileView",
    "PyCall",
    "PyPlot",
    "Revise",
    "Zygote",
]

Pkg.add(pkgs)

ENV["JUPYTER"] = "/opt/miniconda3/envs/jupyter/bin/jupyter"
ENV["PYTHON"]  = "/opt/miniconda3/envs/jupyter/bin/python"
Pkg.build("IJulia")
Pkg.build("PyCall")
