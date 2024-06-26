from vendor.pyBusPirateLite.SPI import SPI

class W25Q64FV(SPI):
    """ Adapted SPI methods for Winbond W25Q64FV flash memory"""

    PAGE_SIZE = 256 # page size in bytes
    MAX_WORDS = PAGE_SIZE * 32768 # max number of words in flash memory

    COMMAND_READ = 0x03
    COMMAND_READ_STATUS_REG_1 = 0x05
    COMMAND_READ_STATUS_REG_2 = 0x35
    COMMAND_WRITE_ENABLE = 0x06

    def __init__(self, portname='', speed=115200, timeout=0.5, connect=True, buzzpirateFirm=True):
        """
        Provide high-speed access to the Bus Pirate SPI hardware.

        This constructor by default connects to the first Bus Pirate it can
        find. If you don't want that, set connect to False.

        Parameters
        ----------
        portname : str
            Name of comport (/dev/bus_pirate or COM3)
        speed : int
            Communication speed, use default of 115200
        timeout : int
            Timeout in s to wait for reply
        connect : bool
            Connect to the Bus Pirate (default)
        buzzpirateFirm : bool
            Indicate if the firmware is https://buzzpirat.com/ or not. The
            behavior of the write_then_read method is different. The
            SPI.write_then_read method of the BPv3.6 firmware is buggy and only
            returns 0x01 when there is data to read. In buzzpirate firmware that
            is fixed.

        Examples
        --------
        >>> from hackPyrateBus.W25Q64FV import W25Q64FV
        >>> winbond = W25Q64FV()
        >>> winbond.pins = W25Q64FV.PIN_POWER | W25Q64FV.PIN_CS
        >>> winbond.config = W25Q64FV.CFG_PUSH_PULL | W25Q64FV.CFG_CLK_EDGE
        >>> winbond.speed = '1MHz'
        """

        super().__init__(portname, speed, timeout, connect)
        self._config = None
        self._speed = None
        self._cs = None
        self._pins = None

        if not buzzpirateFirm:
            self.write_then_read = self.write_then_read_no_iosuccess

    def read(self, addr, amount):
        """
        Read data from flash memory using the write_then_read method. Currently
        this method is slow as hell because the data is sent to the UART before
        pulling the CS pin high (even though in the documentation it says the CS
        pin is pulled high before sending the data).

        Parameters
        ----------
        addr : int
            Three byte address in the flash memory
        amount : int
            The number of bytes to read from the flash memory

        Raises
        ------
        ValueError
            If the address is out of range for the flash memory size

        Examples
        --------
        >>> img = winbond.read(0x000000, winbond.MAX_WORDS)
        >>> with open('flash.img', 'wb') as f:
        ...     f.write(img)
        """

        if addr + amount > self.MAX_WORDS:
            raise ValueError("Out of range for flash memory size")

        res = []
        # the bus pirate write_then_read method can only read 4096 bytes at a time
        while amount > 4096:
            header = [self.COMMAND_READ] + list(addr.to_bytes(3, 'big'))
            r = self.write_then_read(len(header), 4096, header)
            res.extend(r)
            amount -= 4096
            addr += 4096

        header = [self.COMMAND_READ] + list(addr.to_bytes(3, 'big'))
        r = self.write_then_read(len(header), amount, header)
        res.extend(r)

        return bytes(res)

    def store(self, addr, data, chip_erase=False):
        """
        Store data to flash memory. The data is split into PAGE_SIZE byte chunks
        and the method takes care of Write Enable and erasing the minimum
        necessary sectors. It can be forced to erase the entire memory too.

        Parameters
        ----------
        addr : int
            Three byte address in the flash memory
        data : bytes
            The bytes to write to the flash memory
        chip_erase : bool
            Erase the entire memory before writing the data

        Raises
        ------
        ValueError
            If the address is out of range for the flash memory size

        Examples
        --------
        >>> winbond.store(0x000000, b'\x00Hello, world!\xff')
        """

        if addr + len(data) > self.MAX_WORDS:
            raise ValueError("Out of range for flash memory size")

        res = []
        # the bus pirate write_then_read method can only read 4096 bytes at a time
        while amount > 4096:
            header = [self.COMMAND_READ] + list(addr.to_bytes(3, 'big'))
            r = self.write_then_read(len(header), 4096, header)
            res.extend(r)
            amount -= 4096
            addr += 4096

        header = [self.COMMAND_READ] + list(addr.to_bytes(3, 'big'))
        r = self.write_then_read(len(header), amount, header)
        res.extend(r)

        return bytes(res)

    def status_registers(self):
        """
        Returns the status registers of the flash memory.

        Parameters
        ----------

        Examples
        --------
        >>> reg = winbond.read_status_registers()
        """

        # read status register 1
        r = self.write_then_read(1, 1, [self.COMMAND_READ_STATUS_REG_1])
        # read status register 2
        r += self.write_then_read(1, 1, [self.COMMAND_READ_STATUS_REG_2])

        return r

    def write_enable(self):
        """
        Sets the Write Enable Latch (WEL) bit in the Status Register to a 1. The
        WEL bit must be set prior to every Page Program, or Erase operation.

        Parameters
        ----------

        Examples
        --------
        >>> winbond.write_enable()
        """

        self.write_then_read(1, 0, [self.COMMAND_WRITE_ENABLE])
