from vendor.pyBusPirateLite.SPI import SPI

class W25Q64FV(SPI):
    """ Adapted SPI methods for Winbond W25Q64FV flash memory"""

    PAGE_SIZE = 256 # page size in bytes
    MAX_WORDS = PAGE_SIZE * 32768 # max number of words in flash memory

    COMMAND_READ = 0x03

    def __init__(self, portname='', speed=115200, timeout=0.5, connect=True):
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

    def read(self, addr, amount):
        """
        Read data from flash memory using the write_then_read method

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
