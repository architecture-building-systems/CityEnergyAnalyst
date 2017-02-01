from pybps import BPSProject

def main():
    path_to_bps_project = 'L:\Trnsys17\Examples\Parametric_Runs'
    bpsproj = BPSProject(path_to_bps_project)

    bpsproj.add_jobs()
    bpsproj.run()
    bpsproj.jobs2df()

if __name__ == '__main__':
    # freeze_support() here if program needs to be frozen
    main()