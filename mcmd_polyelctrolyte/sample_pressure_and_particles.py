import logging
import os
import pathlib
import pickle
import shutil
import time

import numpy as np

logger = logging.getLogger(__name__)

def sample_all(
        MC, target_sample_size, timeout,
        save_file_path,
        save_file_header : dict = {},
        particle_count_sampling_kwargs = None,
        pressure_sampling_kwargs = None,
        include_kwargs_to_header = True
        #list_to_ndarray = True
        ):
    #start timer
    start_time = time.time()

    #pickle storage, will store on each change
    storage = PickleStorage(save_file_path, write_every=1)

    #add header to stored data
    if include_kwargs_to_header:
        save_file_header.update({'particle_count_sampling_kwargs' : particle_count_sampling_kwargs})
        save_file_header.update({'pressure_sampling_kwargs' : pressure_sampling_kwargs})
    if save_file_header:
        storage.content = save_file_header

    #sample stored as dict of lists
    sample_d = {}
    sample_d.update(save_file_header)
    logger.info((
        "Sampling pressure and particle count... \n",
        f"Target sample size: {target_sample_size} \n",
        f"Timeout: {timeout}s"
        ))
    for i in range(target_sample_size):
        if time.time()-start_time > timeout:
            logger.warning("Timeout is reached")
            sample_d['message'] = "reached_timeout"
            break
        try:
            particles_speciation = MC.sample_particle_count_to_target_error(
                **particle_count_sampling_kwargs
            )
        except Exception as e:
            logger.error('An error occurred during sampling')
            logger.exception(e)
            sample_d['message'] = "error_occurred"
            break

        #probably we can dry run some MD without collecting any data
        try:
            pressure = MC.sample_pressures_to_target_error(
                **pressure_sampling_kwargs
                )
        except Exception as e:
            logger.error('An error occurred during sampling')
            logger.exception(e)
            sample_d['message'] = "error_occurred"
            break

        #discard info about errors
        del particles_speciation['err']
        del particles_speciation['sample_size']
        del pressure['err']
        del pressure['sample_size']
        datum_d = {**particles_speciation, **pressure}

        #to each list in result dict append datum
        append_to_lists_in_dict(sample_d, datum_d)
        logger.info(f"{i+1}/{target_sample_size}")
        logger.debug(datum_d)

        #save updated data to pickle storage
        storage.content = sample_d

    logger.info(f'Sampling is done, data are stored to {save_file_path}')
    return sample_d


class PickleStorage:
    def __init__(
            self,
            path_to_file,
            init_content = None,
            *arg,
            write_every = 10,
            ) -> None:
        self.path = pathlib.Path(path_to_file)
        self.backup_path = self.path.parent / ('~'+self.path.name + '.bak')
        self.max_changes_before_backup = write_every
        self.changes_counter = 0
        self._content = None
        if init_content is not None:
            self.content = init_content

    def backup(self):
        try:
            #logger.debug("Backup data")
            shutil.copy(self.path, self.backup_path)
        except FileNotFoundError as e:
            pass

    def __del__(self):
        if (self._content is not None) and (self.changes_counter>0):
            with open(self.path, 'wb') as f:
                pickle.dump(self._content, f)
        try:
            os.unlink(self.backup_path)
            #logging.info("Backup deleted")
        except FileNotFoundError as e:
            pass

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, obj):
        #if self._content == obj:
        #    return
        self._content = obj
        #keep track of changes
        self.changes_counter += 1
        #if already too many changes without backup
        if self.changes_counter>=self.max_changes_before_backup:
            self.flush()

    @content.getter
    def content(self):
        #if self.init_mtime != os.stat(self.path):
        #    logger.warning("File changed between operations")
        #    with open(self.path, 'rb') as f:
        #        self._content = pickle.load(f)
        if self._content is None:
            with open(self.path, 'rb') as f:
                self._content = pickle.load(f)
        return self._content

    def reload(self):
        with open(self.path, 'rb') as f:
            self._content = pickle.load(f)
            self.changes_counter = 0
        self.backup()

    def flush(self):
        self.backup()
        #rewrite existing
        with open(self.path, 'wb') as f:
            pickle.dump(self._content, f)
        self.changes_counter = 0


def append_to_lists_in_dict(dict_A, dict_B):
    for k, v in dict_B.items():
        while True:
            try:
                dict_A[k].append(v)
                break
            except KeyError:
                dict_A[k] = []
            except AttributeError:
                dict_A[k] = [dict_A[k]]
